"""fingerprint composition wrapper — 계산 + group UPSERT + alert + 마킹.

설계서: 2026-05-01-error-log-phase3-design.md §2.4, §3.3
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_event import LogEvent
from app.services import error_group_service, fingerprint_service, log_alert_service


async def process(db: AsyncSession, event: LogEvent) -> None:
    """fingerprint 계산 → ErrorGroup UPSERT → fingerprinted_at 마킹 + commit → 신규면 알림.

    설계서 §2.4 — commit 후 알림 (Phase 6 학습: DB 일관 상태에서 발송).
    """
    fingerprint = fingerprint_service.compute(
        exception_class=event.exception_class or "UnknownError",
        stack_frames=event.stack_frames,
        exception_message=event.exception_message,
    )

    result = await error_group_service.upsert(
        db, project_id=event.project_id, fingerprint=fingerprint, event=event,
    )

    event.fingerprint = fingerprint
    event.fingerprinted_at = datetime.utcnow()
    await db.commit()

    # B-lite — 신규 fingerprint 1회 알림
    if result.is_new:
        await log_alert_service.notify_new_error(
            db, project_id=event.project_id, group=result.group, event=event,
        )
