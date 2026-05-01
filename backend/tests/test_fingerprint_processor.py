"""fingerprint_processor 단위 테스트.

설계서: 2026-05-01-error-log-phase3-design.md §2.4, §3.3
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.log_event import LogEvent, LogLevel
from app.models.project import Project
from app.models.workspace import Workspace
from app.services import fingerprint_processor


async def _seed(db: AsyncSession) -> tuple[Project, LogEvent]:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.flush()
    event = LogEvent(
        project_id=proj.id, level=LogLevel.ERROR,
        message="boom", logger_name="app.x", version_sha="a" * 40,
        environment="production", hostname="h",
        emitted_at=datetime.utcnow(), received_at=datetime.utcnow(),
        exception_class="KeyError", exception_message="'preference'",
        stack_frames=[
            {"filename": "/app/backend/x.py", "lineno": 10, "name": "do_thing"},
        ],
    )
    db.add(event)
    await db.commit()
    await db.refresh(proj)
    await db.refresh(event)
    return proj, event


async def test_process_normal_path(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """fingerprint 계산 + group UPSERT + fingerprinted_at 마킹 + commit."""
    proj, event = await _seed(async_session)

    notifications: list = []
    async def fake_notify(db, *, project_id, group, event):
        notifications.append((project_id, group.id))

    import app.services.log_alert_service as alert_mod
    monkeypatch.setattr(alert_mod, "notify_new_error", fake_notify)

    await fingerprint_processor.process(async_session, event)

    await async_session.refresh(event)
    assert event.fingerprint is not None
    assert len(event.fingerprint) == 40
    assert event.fingerprinted_at is not None

    # 신규 group 만들어짐
    groups = (await async_session.execute(
        select(ErrorGroup).where(ErrorGroup.project_id == proj.id)
    )).scalars().all()
    assert len(groups) == 1
    assert groups[0].fingerprint == event.fingerprint

    # 신규 → notify 호출
    assert len(notifications) == 1


async def test_process_existing_group_no_notify(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """기존 group → notify_new_error 호출 안 함."""
    proj, event1 = await _seed(async_session)

    notifications: list = []
    async def fake_notify(db, *, project_id, group, event):
        notifications.append((project_id, group.id))

    import app.services.log_alert_service as alert_mod
    monkeypatch.setattr(alert_mod, "notify_new_error", fake_notify)

    # 1차 — 신규 → notify 1회
    await fingerprint_processor.process(async_session, event1)
    assert len(notifications) == 1

    # 2차 — 같은 fingerprint event
    event2 = LogEvent(
        project_id=proj.id, level=LogLevel.ERROR,
        message="boom2", logger_name="app.x", version_sha="b" * 40,
        environment="production", hostname="h",
        emitted_at=datetime.utcnow(), received_at=datetime.utcnow(),
        exception_class="KeyError", exception_message="'preference'",
        stack_frames=[
            {"filename": "/app/backend/x.py", "lineno": 10, "name": "do_thing"},
        ],
    )
    async_session.add(event2)
    await async_session.commit()
    await async_session.refresh(event2)

    await fingerprint_processor.process(async_session, event2)

    # 기존 group → notify 호출 안 함 (count 1 그대로)
    assert len(notifications) == 1


async def test_process_handles_no_stack_frames(async_session: AsyncSession):
    """stack_frames 없는 event → fallback fingerprint 동작."""
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(workspace_id=ws.id, name="p")
    async_session.add(proj)
    await async_session.flush()
    event = LogEvent(
        project_id=proj.id, level=LogLevel.ERROR,
        message="boom", logger_name="app.x", version_sha="a" * 40,
        environment="production", hostname="h",
        emitted_at=datetime.utcnow(), received_at=datetime.utcnow(),
        exception_class="KeyError", exception_message="'preference'",
        stack_frames=None,
    )
    async_session.add(event)
    await async_session.commit()
    await async_session.refresh(event)

    await fingerprint_processor.process(async_session, event)
    await async_session.refresh(event)

    assert event.fingerprint is not None
    assert event.fingerprinted_at is not None


async def test_process_uses_unknown_class_when_missing(async_session: AsyncSession):
    """exception_class 가 None 이면 'UnknownError' 로 처리."""
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(workspace_id=ws.id, name="p")
    async_session.add(proj)
    await async_session.flush()
    event = LogEvent(
        project_id=proj.id, level=LogLevel.ERROR,
        message="boom", logger_name="app.x", version_sha="a" * 40,
        environment="production", hostname="h",
        emitted_at=datetime.utcnow(), received_at=datetime.utcnow(),
        exception_class=None,  # 명시적으로 None
        exception_message="something",
        stack_frames=None,
    )
    async_session.add(event)
    await async_session.commit()
    await async_session.refresh(event)

    await fingerprint_processor.process(async_session, event)
    await async_session.refresh(event)
    assert event.fingerprint is not None

    groups = (await async_session.execute(
        select(ErrorGroup).where(ErrorGroup.project_id == proj.id)
    )).scalars().all()
    assert len(groups) == 1
    assert groups[0].exception_class == "UnknownError"
