"""LogEvent / ErrorGroup 조회 + Git 컨텍스트 join.

설계서: 2026-05-01-error-log-phase4-query-design.md §3.1
spec §6.2 의 데이터 흐름 그대로.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.log_event import LogEvent, LogLevel


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
