"""log-health 메트릭 계산.

설계서: 2026-04-26-error-log-design.md §7 Health 표.
"""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_event import LogEvent, UNKNOWN_SHA


_WINDOW = timedelta(hours=24)
_DRIFT_THRESHOLD = timedelta(hours=1)


async def compute_health(
    db: AsyncSession, *, project_id: UUID,
) -> dict[str, int | float]:
    """24h 윈도우 헬스 메트릭 계산.

    Returns dict (LogHealthResponse 와 동일 키):
      total_events_24h, unknown_sha_count_24h, unknown_sha_ratio_24h,
      clock_drift_count_24h.
    """
    now = datetime.utcnow()
    window_start = now - _WINDOW

    # 단일 SQL — 3 집계 동시.
    drift_seconds = _DRIFT_THRESHOLD.total_seconds()
    stmt = select(
        func.count().label("total"),
        func.count().filter(LogEvent.version_sha == UNKNOWN_SHA).label("unknown"),
        func.count().filter(
            func.abs(
                func.extract("epoch", LogEvent.received_at - LogEvent.emitted_at)
            ) > drift_seconds
        ).label("drift"),
    ).where(
        LogEvent.project_id == project_id,
        LogEvent.received_at >= window_start,
    )

    row = (await db.execute(stmt)).one()
    total = int(row.total or 0)
    unknown = int(row.unknown or 0)
    drift = int(row.drift or 0)

    ratio = unknown / total if total > 0 else 0.0

    return {
        "total_events_24h": total,
        "unknown_sha_count_24h": unknown,
        "unknown_sha_ratio_24h": ratio,
        "clock_drift_count_24h": drift,
    }
