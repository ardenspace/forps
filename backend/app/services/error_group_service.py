"""ErrorGroup UPSERT + 자동 status 전이.

설계서: 2026-05-01-error-log-phase3-design.md §2.3
race-free: with_for_update + IntegrityError SAVEPOINT fallback (Phase 2 record_push_event 패턴).
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.log_event import LogEvent

logger = logging.getLogger(__name__)


@dataclass
class GroupResult:
    group: ErrorGroup
    is_new: bool
    transitioned_to_regression: bool


def _select_for_update(project_id: UUID, fingerprint: str):
    return (
        select(ErrorGroup)
        .where(
            ErrorGroup.project_id == project_id,
            ErrorGroup.fingerprint == fingerprint,
        )
        .with_for_update()
    )


def _apply_update(group: ErrorGroup, event: LogEvent) -> bool:
    """기존 group 에 event 반영. transitioned_to_regression 반환."""
    transitioned = False
    if group.status == ErrorGroupStatus.RESOLVED:
        group.status = ErrorGroupStatus.REGRESSED
        transitioned = True
    group.last_seen_at = event.received_at
    group.last_seen_version_sha = event.version_sha
    group.event_count += 1
    if event.exception_message:
        group.exception_message_sample = event.exception_message
    return transitioned


async def upsert(
    db: AsyncSession,
    *,
    project_id: UUID,
    fingerprint: str,
    event: LogEvent,
) -> GroupResult:
    """fingerprint 별 ErrorGroup UPSERT + 자동 status 전이.

    1차: SELECT FOR UPDATE — 있으면 UPDATE 분기.
    2차 (없으면): SAVEPOINT INSERT — UNIQUE conflict catch 시 SELECT + UPDATE fallback.
    """
    stmt = _select_for_update(project_id, fingerprint)
    group = (await db.execute(stmt)).scalar_one_or_none()

    if group is not None:
        transitioned = _apply_update(group, event)
        await db.flush()
        return GroupResult(group=group, is_new=False, transitioned_to_regression=transitioned)

    # 신규 INSERT — UNIQUE conflict race 가능 → SAVEPOINT
    new_group = ErrorGroup(
        project_id=project_id,
        fingerprint=fingerprint,
        exception_class=event.exception_class or "UnknownError",
        exception_message_sample=event.exception_message,
        first_seen_at=event.received_at,
        first_seen_version_sha=event.version_sha,
        last_seen_at=event.received_at,
        last_seen_version_sha=event.version_sha,
        event_count=1,
        status=ErrorGroupStatus.OPEN,
    )
    try:
        async with db.begin_nested():
            db.add(new_group)
            await db.flush()
        return GroupResult(group=new_group, is_new=True, transitioned_to_regression=False)
    except IntegrityError:
        logger.info(
            "ErrorGroup UNIQUE conflict (race) for project=%s fingerprint=%s — fallback UPDATE",
            project_id, fingerprint,
        )
        existing = (await db.execute(_select_for_update(project_id, fingerprint))).scalar_one_or_none()
        if existing is None:
            raise
        transitioned = _apply_update(existing, event)
        await db.flush()
        return GroupResult(group=existing, is_new=False, transitioned_to_regression=transitioned)


# ---- 사용자 액션 기반 status 전이 ----

# 합법 전이 매트릭스: (현재 status, action) -> 다음 status
_LEGAL_TRANSITIONS: dict[tuple[ErrorGroupStatus, str], ErrorGroupStatus] = {
    (ErrorGroupStatus.OPEN, "resolve"): ErrorGroupStatus.RESOLVED,
    (ErrorGroupStatus.OPEN, "ignore"): ErrorGroupStatus.IGNORED,
    (ErrorGroupStatus.RESOLVED, "reopen"): ErrorGroupStatus.OPEN,
    (ErrorGroupStatus.IGNORED, "unmute"): ErrorGroupStatus.OPEN,
    (ErrorGroupStatus.REGRESSED, "resolve"): ErrorGroupStatus.RESOLVED,
    (ErrorGroupStatus.REGRESSED, "reopen"): ErrorGroupStatus.OPEN,
}


async def transition_status(
    db: AsyncSession,
    group: ErrorGroup,
    *,
    action: str,
    user_id: UUID,
    resolved_in_version_sha: str | None,
) -> ErrorGroup:
    """사용자 액션으로 ErrorGroup status 전이. 합법 전이만 허용.

    Raises:
        ValueError: 불법 전이 ((현재, action) tuple 이 _LEGAL_TRANSITIONS 에 없음).

    Note: 호출자(endpoint)가 commit 책임 — `upsert` 와 같은 패턴.
    """
    key = (group.status, action)
    next_status = _LEGAL_TRANSITIONS.get(key)
    if next_status is None:
        raise ValueError(
            f"illegal transition: {group.status.value} + {action!r}"
        )

    group.status = next_status

    if next_status == ErrorGroupStatus.RESOLVED:
        group.resolved_at = datetime.utcnow()
        group.resolved_by_user_id = user_id
        group.resolved_in_version_sha = resolved_in_version_sha
    elif next_status == ErrorGroupStatus.OPEN and action == "reopen":
        # RESOLVED → OPEN 시 audit 필드 클리어.
        group.resolved_at = None
        group.resolved_by_user_id = None
        group.resolved_in_version_sha = None

    await db.flush()
    return group
