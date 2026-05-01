"""log_alert_service 단위 테스트 (B-lite — notify_new_error).

설계서: 2026-05-01-error-log-phase3-design.md §2.5, §3.4
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.log_event import LogEvent, LogLevel
from app.models.project import Project
from app.models.workspace import Workspace
from app.services import log_alert_service


async def _seed(
    db: AsyncSession,
    *,
    discord_webhook_url: str | None = "https://discord.com/api/webhooks/1/abc",
    last_alerted_new_at: datetime | None = None,
) -> tuple[Project, ErrorGroup, LogEvent]:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(
        workspace_id=ws.id, name="p",
        discord_webhook_url=discord_webhook_url,
    )
    db.add(proj)
    await db.flush()

    group = ErrorGroup(
        project_id=proj.id, fingerprint="fp-1",
        exception_class="KeyError", exception_message_sample="'preference'",
        first_seen_at=datetime.utcnow(), first_seen_version_sha="a" * 40,
        last_seen_at=datetime.utcnow(), last_seen_version_sha="a" * 40,
        event_count=1, status=ErrorGroupStatus.OPEN,
        last_alerted_new_at=last_alerted_new_at,
    )
    db.add(group)

    event = LogEvent(
        project_id=proj.id, level=LogLevel.ERROR,
        message="boom", logger_name="app.x",
        version_sha="a" * 40,
        environment="production", hostname="h",
        emitted_at=datetime.utcnow(), received_at=datetime.utcnow(),
        exception_class="KeyError", exception_message="'preference'",
    )
    db.add(event)
    await db.commit()
    await db.refresh(proj)
    await db.refresh(group)
    await db.refresh(event)
    return proj, group, event


async def test_notify_new_error_dispatches_and_marks(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """last_alerted_new_at IS NULL → dispatcher 호출 + 마킹."""
    proj, group, event = await _seed(async_session)

    sent: list[tuple] = []
    async def fake_dispatch(db, project, content):
        sent.append((project.id, content))

    import app.services.notification_dispatcher as dispatcher_mod
    monkeypatch.setattr(dispatcher_mod, "dispatch_discord_alert", fake_dispatch)

    await log_alert_service.notify_new_error(
        async_session, project_id=proj.id, group=group, event=event,
    )

    assert len(sent) == 1
    project_id, content = sent[0]
    assert project_id == proj.id
    assert "🆕" in content
    assert "KeyError" in content
    assert "production" in content

    await async_session.refresh(group)
    assert group.last_alerted_new_at is not None


async def test_notify_new_error_skipped_when_already_alerted(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """last_alerted_new_at 이미 set → no-op."""
    proj, group, event = await _seed(
        async_session, last_alerted_new_at=datetime.utcnow(),
    )

    sent: list = []
    async def fake_dispatch(db, project, content):
        sent.append((project.id, content))

    import app.services.notification_dispatcher as dispatcher_mod
    monkeypatch.setattr(dispatcher_mod, "dispatch_discord_alert", fake_dispatch)

    await log_alert_service.notify_new_error(
        async_session, project_id=proj.id, group=group, event=event,
    )

    assert sent == []  # cooldown — 호출 안 함


async def test_notify_new_error_skipped_when_project_missing(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """project not found → no-op."""
    sent: list = []
    async def fake_dispatch(db, project, content):
        sent.append((project.id, content))

    import app.services.notification_dispatcher as dispatcher_mod
    monkeypatch.setattr(dispatcher_mod, "dispatch_discord_alert", fake_dispatch)

    fake_group = ErrorGroup(
        project_id=uuid.uuid4(),  # 존재 X
        fingerprint="fp-x",
        exception_class="KeyError", exception_message_sample="x",
        first_seen_at=datetime.utcnow(), first_seen_version_sha="a" * 40,
        last_seen_at=datetime.utcnow(), last_seen_version_sha="a" * 40,
        event_count=1, status=ErrorGroupStatus.OPEN,
    )
    fake_event = LogEvent(
        project_id=uuid.uuid4(), level=LogLevel.ERROR,
        message="x", logger_name="app", version_sha="a" * 40,
        environment="production", hostname="h",
        emitted_at=datetime.utcnow(), received_at=datetime.utcnow(),
    )

    await log_alert_service.notify_new_error(
        async_session, project_id=uuid.uuid4(), group=fake_group, event=fake_event,
    )

    assert sent == []
