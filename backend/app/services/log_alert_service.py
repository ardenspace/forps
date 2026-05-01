"""Discord 알림 — 본 phase 는 신규 fingerprint 알림만 (B-lite).

설계서: 2026-05-01-error-log-phase3-design.md §2.5
spike / regression 은 Phase 6 본편에서 추가.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup
from app.models.log_event import LogEvent
from app.models.project import Project
from app.services import notification_dispatcher

logger = logging.getLogger(__name__)


async def notify_new_error(
    db: AsyncSession,
    *,
    project_id: UUID,
    group: ErrorGroup,
    event: LogEvent,
) -> None:
    """신규 fingerprint 1회 Discord 알림. cooldown — group당 1회만.

    notification_dispatcher 통과 (Phase 6 disable 정책 자동 적용).
    """
    project = await db.get(Project, project_id)
    if project is None:
        return
    if group.last_alerted_new_at is not None:
        # Single-caller invariant: 본 함수는 fingerprint_processor 의 is_new=True 분기에서만 호출됨.
        # error_group_service.upsert 의 SAVEPOINT race 가 loser 에게 is_new=False 줘 단일 caller 보장.
        # 향후 다른 caller (Phase 6 spike/regression) 추가 시 with_for_update 재검증 필요.
        return

    short_sha = (
        event.version_sha[:7] if event.version_sha != "unknown" else "unknown"
    )
    msg_first = (group.exception_message_sample or "").splitlines()[0][:200]
    content = (
        f"🆕 **새 에러** — {group.exception_class}\n"
        f"메시지: {msg_first}\n"
        f"첫 발생: `{short_sha}` ({event.environment})"
    )

    try:
        await notification_dispatcher.dispatch_discord_alert(db, project, content)
    except Exception:
        logger.exception(
            "Discord alert dispatch failed for new error group=%s", group.id,
        )
        return

    group.last_alerted_new_at = datetime.utcnow()
    await db.commit()
