"""log_query_service 단위 테스트.

설계서: 2026-05-01-error-log-phase4-query-design.md §3.1
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.log_event import LogEvent, LogLevel
from app.models.project import Project
from app.models.workspace import Workspace
from app.services import log_query_service


async def _seed_project(db: AsyncSession) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


def _make_group(
    proj: Project, *, fingerprint: str = "fp-1",
    status: ErrorGroupStatus = ErrorGroupStatus.OPEN,
    last_seen_at: datetime | None = None,
) -> ErrorGroup:
    now = datetime.utcnow()
    return ErrorGroup(
        project_id=proj.id, fingerprint=fingerprint,
        exception_class="KeyError", exception_message_sample="x",
        first_seen_at=now, first_seen_version_sha="a" * 40,
        last_seen_at=last_seen_at or now, last_seen_version_sha="a" * 40,
        event_count=1, status=status,
    )


# ---- list_groups ----

async def test_list_groups_returns_all_when_no_filter(async_session: AsyncSession):
    """필터 없음 — 모든 group + total 반환."""
    proj = await _seed_project(async_session)
    g1 = _make_group(proj, fingerprint="fp-a")
    g2 = _make_group(proj, fingerprint="fp-b", status=ErrorGroupStatus.RESOLVED)
    async_session.add_all([g1, g2])
    await async_session.commit()

    rows, total = await log_query_service.list_groups(
        async_session, project_id=proj.id,
    )
    assert total == 2
    assert len(rows) == 2


async def test_list_groups_filter_by_status(async_session: AsyncSession):
    """status=OPEN 필터."""
    proj = await _seed_project(async_session)
    g_open = _make_group(proj, fingerprint="fp-a", status=ErrorGroupStatus.OPEN)
    g_resolved = _make_group(proj, fingerprint="fp-b", status=ErrorGroupStatus.RESOLVED)
    async_session.add_all([g_open, g_resolved])
    await async_session.commit()

    rows, total = await log_query_service.list_groups(
        async_session, project_id=proj.id, status=ErrorGroupStatus.OPEN,
    )
    assert total == 1
    assert rows[0].fingerprint == "fp-a"


async def test_list_groups_filter_by_since(async_session: AsyncSession):
    """since=... 필터 (last_seen_at >= since)."""
    proj = await _seed_project(async_session)
    cutoff = datetime(2026, 5, 1, 10, 0)
    old = _make_group(proj, fingerprint="fp-old", last_seen_at=datetime(2026, 4, 30, 23, 0))
    new = _make_group(proj, fingerprint="fp-new", last_seen_at=datetime(2026, 5, 1, 11, 0))
    async_session.add_all([old, new])
    await async_session.commit()

    rows, total = await log_query_service.list_groups(
        async_session, project_id=proj.id, since=cutoff,
    )
    assert total == 1
    assert rows[0].fingerprint == "fp-new"


async def test_list_groups_pagination_total_correct(async_session: AsyncSession):
    """offset/limit — total 은 전체, items 는 limit 만큼."""
    proj = await _seed_project(async_session)
    for i in range(5):
        async_session.add(_make_group(proj, fingerprint=f"fp-{i}"))
    await async_session.commit()

    rows, total = await log_query_service.list_groups(
        async_session, project_id=proj.id, offset=0, limit=2,
    )
    assert total == 5
    assert len(rows) == 2

    rows2, total2 = await log_query_service.list_groups(
        async_session, project_id=proj.id, offset=4, limit=2,
    )
    assert total2 == 5
    assert len(rows2) == 1  # 5 - 4 = 1
