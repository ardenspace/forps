"""project_service 회귀 — Phase 6 의 URL 변경 시 자동 reset.

설계서: 2026-05-01-phase-6-discord-notifications-design.md §3.7
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.workspace import Workspace
from app.schemas.project import ProjectUpdate
from app.services import project_service


async def test_update_project_resets_discord_counter_when_url_changes(
    async_session: AsyncSession,
):
    """update_project 가 discord_webhook_url 변경 감지 시 counter / disabled_at reset."""
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(
        workspace_id=ws.id, name="p",
        discord_webhook_url="https://discord.com/api/webhooks/1/old",
        discord_consecutive_failures=3,
        discord_disabled_at=datetime.utcnow(),
    )
    async_session.add(proj)
    await async_session.commit()
    await async_session.refresh(proj)

    update = ProjectUpdate(discord_webhook_url="https://discord.com/api/webhooks/1/new")
    # update_project signature: (db, project, data) — project object, not id
    updated = await project_service.update_project(async_session, proj, update)

    assert updated is not None
    assert updated.discord_webhook_url == "https://discord.com/api/webhooks/1/new"
    assert updated.discord_consecutive_failures == 0
    assert updated.discord_disabled_at is None
