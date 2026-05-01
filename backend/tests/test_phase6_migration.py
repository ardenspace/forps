"""Phase 6 마이그레이션 회귀 — discord_consecutive_failures / discord_disabled_at 컬럼 추가.

설계서: 2026-05-01-phase-6-discord-notifications-design.md §3.3
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.workspace import Workspace


async def test_phase6_columns_exist(async_session: AsyncSession):
    """alembic upgrade 후 Project 에 두 컬럼 존재 + 기본값 적용."""
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(workspace_id=ws.id, name="p")
    async_session.add(proj)
    await async_session.commit()
    await async_session.refresh(proj)

    assert proj.discord_consecutive_failures == 0
    assert proj.discord_disabled_at is None


async def test_phase6_columns_set_and_persist(async_session: AsyncSession):
    """수동으로 set 한 값이 round-trip 으로 보존."""
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(workspace_id=ws.id, name="p")
    async_session.add(proj)
    await async_session.commit()
    await async_session.refresh(proj)

    now = datetime.utcnow()
    proj.discord_consecutive_failures = 3
    proj.discord_disabled_at = now
    await async_session.commit()
    await async_session.refresh(proj)

    assert proj.discord_consecutive_failures == 3
    assert proj.discord_disabled_at is not None
    # microseconds 손실 가능성 회피 — 같은 second 인지만 확인
    assert proj.discord_disabled_at.replace(microsecond=0) == now.replace(microsecond=0)
