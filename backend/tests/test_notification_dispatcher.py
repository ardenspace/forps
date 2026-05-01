"""notification_dispatcher 단위 테스트.

설계서: 2026-05-01-phase-6-discord-notifications-design.md §3.1
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.workspace import Workspace
from app.services import notification_dispatcher


async def _seed_project(
    db: AsyncSession,
    *,
    discord_webhook_url: str | None = None,
    discord_disabled_at: datetime | None = None,
    discord_consecutive_failures: int = 0,
) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(
        workspace_id=ws.id, name="p",
        discord_webhook_url=discord_webhook_url,
        discord_disabled_at=discord_disabled_at,
        discord_consecutive_failures=discord_consecutive_failures,
    )
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def test_dispatch_skipped_when_url_missing(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """discord_webhook_url IS NULL → send_webhook 호출 안 함."""
    proj = await _seed_project(async_session, discord_webhook_url=None)

    sent: list = []
    async def fake_send(content, url):
        sent.append((content, url))

    import app.services.discord_service as discord_mod
    monkeypatch.setattr(discord_mod, "send_webhook", fake_send)

    await notification_dispatcher.dispatch_discord_alert(async_session, proj, "hello")

    assert sent == []
    await async_session.refresh(proj)
    assert proj.discord_consecutive_failures == 0
    assert proj.discord_disabled_at is None


async def test_dispatch_skipped_when_disabled(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """discord_disabled_at IS NOT NULL → send_webhook 호출 안 함, counter 변동 없음."""
    proj = await _seed_project(
        async_session,
        discord_webhook_url="https://discord.com/api/webhooks/1/abc",
        discord_disabled_at=datetime.utcnow(),
        discord_consecutive_failures=3,
    )

    sent: list = []
    async def fake_send(content, url):
        sent.append((content, url))

    import app.services.discord_service as discord_mod
    monkeypatch.setattr(discord_mod, "send_webhook", fake_send)

    await notification_dispatcher.dispatch_discord_alert(async_session, proj, "hello")

    assert sent == []
    await async_session.refresh(proj)
    assert proj.discord_consecutive_failures == 3
    assert proj.discord_disabled_at is not None


async def test_dispatch_resets_counter_on_success(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """send 성공 시 counter > 0 이면 0 reset."""
    proj = await _seed_project(
        async_session,
        discord_webhook_url="https://discord.com/api/webhooks/1/abc",
        discord_consecutive_failures=2,
    )

    sent: list = []
    async def fake_send(content, url):
        sent.append((content, url))

    import app.services.discord_service as discord_mod
    monkeypatch.setattr(discord_mod, "send_webhook", fake_send)

    await notification_dispatcher.dispatch_discord_alert(async_session, proj, "hello")

    assert len(sent) == 1
    await async_session.refresh(proj)
    assert proj.discord_consecutive_failures == 0
    assert proj.discord_disabled_at is None


async def test_dispatch_increments_and_disables_after_threshold(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """send 실패 3회 누적 시 disabled_at 자동 설정."""
    proj = await _seed_project(
        async_session,
        discord_webhook_url="https://discord.com/api/webhooks/1/abc",
        discord_consecutive_failures=2,
    )

    async def boom_send(content, url):
        raise RuntimeError("discord 503")

    import app.services.discord_service as discord_mod
    monkeypatch.setattr(discord_mod, "send_webhook", boom_send)

    await notification_dispatcher.dispatch_discord_alert(async_session, proj, "hello")

    await async_session.refresh(proj)
    assert proj.discord_consecutive_failures == 3
    assert proj.discord_disabled_at is not None
