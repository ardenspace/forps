"""부팅 시 미처리 LogEvent 회수 — fingerprint 처리.

설계서: 2026-05-01-error-log-phase3-design.md §2.7, §3.6
chunked 100건/batch — 큰 backlog 안전. fresh session per event (Phase 4 학습).
"""

import logging

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.log_event import LogEvent, LogLevel
from app.services import fingerprint_processor

logger = logging.getLogger(__name__)

REAPER_BATCH_SIZE = 100


async def run_reaper_once() -> None:
    """level >= ERROR AND fingerprinted_at IS NULL 회수.

    `idx_log_unfingerprinted` partial index 사용 (Phase 1 alembic 이미 생성).
    received_at ASC — 오래된 것 우선.
    """
    while True:
        async with AsyncSessionLocal() as lookup_db:
            stmt = (
                select(LogEvent.id)
                .where(LogEvent.level.in_([LogLevel.ERROR, LogLevel.CRITICAL]))
                .where(LogEvent.fingerprinted_at.is_(None))
                .order_by(LogEvent.received_at.asc())
                .limit(REAPER_BATCH_SIZE)
            )
            ids = (await lookup_db.execute(stmt)).scalars().all()

        if not ids:
            break

        for event_id in ids:
            try:
                async with AsyncSessionLocal() as inner_db:
                    event = await inner_db.get(LogEvent, event_id)
                    if event is None or event.fingerprinted_at is not None:
                        continue
                    await fingerprint_processor.process(inner_db, event)
            except Exception:
                logger.exception("reaper failed for log event %s", event_id)
