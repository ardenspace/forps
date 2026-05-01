"""LogEvent / ErrorGroup 조회 + Git 컨텍스트 join.

설계서: 2026-05-01-error-log-phase4-query-design.md §3.1
spec §6.2 의 데이터 흐름 그대로.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.git_push_event import GitPushEvent
from app.models.handoff import Handoff
from app.models.log_event import LogEvent, LogLevel
from app.models.task import Task


async def list_groups(
    db: AsyncSession,
    *,
    project_id: UUID,
    status: ErrorGroupStatus | None = None,
    since: datetime | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[ErrorGroup], int]:
    """ErrorGroup 목록. 필터 + offset/limit. last_seen_at desc.

    environment 필터 미포함 (v1) — ErrorGroup 자체엔 environment 컬럼 없음.
    """
    base = select(ErrorGroup).where(ErrorGroup.project_id == project_id)
    count_base = select(func.count()).select_from(ErrorGroup).where(
        ErrorGroup.project_id == project_id
    )

    if status is not None:
        base = base.where(ErrorGroup.status == status)
        count_base = count_base.where(ErrorGroup.status == status)
    if since is not None:
        base = base.where(ErrorGroup.last_seen_at >= since)
        count_base = count_base.where(ErrorGroup.last_seen_at >= since)

    base = base.order_by(ErrorGroup.last_seen_at.desc()).offset(offset).limit(limit)

    rows = (await db.execute(base)).scalars().all()
    total = (await db.execute(count_base)).scalar_one()
    return list(rows), total


_RECENT_EVENTS_LIMIT = 50


async def _find_previous_good_sha(
    db: AsyncSession,
    *,
    project_id: UUID,
    environment: str,
    target_fingerprint: str,
    before_received_at: datetime,
) -> str | None:
    """직전 정상 SHA — LEFT JOIN + IS NULL 패턴.

    설계서 §2.2.
    같은 environment 에서 target_fingerprint 가 *없었던* 가장 최근 SHA.
    """
    le = LogEvent.__table__.alias("le")
    le_target = LogEvent.__table__.alias("le_target")
    # DISTINCT 불필요 — LIMIT 1 으로 가장 최근 1건만 반환 (SHA 1 개).
    stmt = (
        select(le.c.version_sha)
        .select_from(
            le.outerjoin(
                le_target,
                (le_target.c.project_id == le.c.project_id)
                & (le_target.c.environment == le.c.environment)
                & (le_target.c.version_sha == le.c.version_sha)
                & (le_target.c.fingerprint == target_fingerprint),
            )
        )
        .where(
            le.c.project_id == project_id,
            le.c.environment == environment,
            le.c.received_at < before_received_at,
            le.c.version_sha != "unknown",
            le_target.c.id.is_(None),
        )
        .order_by(le.c.received_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _collect_git_context(
    db: AsyncSession,
    *,
    project_id: UUID,
    version_shas: set[str],
) -> dict:
    """3 단일 SQL — handoffs / tasks (archived 포함) / push_events join.

    push_event 는 received_at 오름차순 첫 번째 (spec §6.2 'first_seen').
    """
    if not version_shas:
        return {"handoffs": [], "tasks": [], "git_push_event": None}

    handoffs = (await db.execute(
        select(Handoff).where(
            Handoff.project_id == project_id,
            Handoff.commit_sha.in_(version_shas),
        )
    )).scalars().all()

    tasks = (await db.execute(
        select(Task).where(
            Task.project_id == project_id,
            Task.last_commit_sha.in_(version_shas),
        )
        # archived 포함 (spec §4.2)
    )).scalars().all()

    push_events = (await db.execute(
        select(GitPushEvent).where(
            GitPushEvent.project_id == project_id,
            GitPushEvent.head_commit_sha.in_(version_shas),
        )
    )).scalars().all()

    first_push = sorted(push_events, key=lambda e: e.received_at)[0] if push_events else None

    return {
        "handoffs": list(handoffs),
        "tasks": list(tasks),
        "git_push_event": first_push,
    }


async def get_group_detail(
    db: AsyncSession,
    *,
    project_id: UUID,
    group_id: UUID,
) -> dict | None:
    """ErrorGroup 상세 + recent events + git 컨텍스트 + 직전 정상 SHA.

    None — group 미존재 또는 다른 project 소속.
    """
    group = await db.get(ErrorGroup, group_id)
    if group is None or group.project_id != project_id:
        return None

    events_stmt = (
        select(LogEvent)
        .where(LogEvent.fingerprint == group.fingerprint)
        .where(LogEvent.project_id == project_id)
        .order_by(LogEvent.received_at.desc())
        .limit(_RECENT_EVENTS_LIMIT)
    )
    recent_events = (await db.execute(events_stmt)).scalars().all()

    shas = {
        e.version_sha for e in recent_events
        if e.version_sha and e.version_sha != "unknown"
    }
    git_context = await _collect_git_context(
        db, project_id=project_id, version_shas=shas,
    )

    previous_good_sha: str | None = None
    if recent_events:
        first_event = min(recent_events, key=lambda e: e.received_at)
        previous_good_sha = await _find_previous_good_sha(
            db,
            project_id=project_id,
            environment=first_event.environment,
            target_fingerprint=group.fingerprint,
            before_received_at=group.first_seen_at,
        )

    return {
        "group": group,
        "recent_events": list(recent_events),
        "git_context": {
            "first_seen": git_context,
            "previous_good_sha": previous_good_sha,
        },
    }
