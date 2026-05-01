"""error_group_service 단위 테스트.

설계서: 2026-05-01-error-log-phase3-design.md §2.3
"""

import asyncio
import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.log_event import LogEvent, LogLevel
from app.models.project import Project
from app.models.workspace import Workspace
from app.services import error_group_service


async def _seed_project(db: AsyncSession) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


def _make_event(proj: Project, *, version_sha: str = "a" * 40, msg: str = "boom") -> LogEvent:
    return LogEvent(
        project_id=proj.id,
        level=LogLevel.ERROR,
        message=msg,
        logger_name="app.test",
        version_sha=version_sha,
        environment="production",
        hostname="h",
        emitted_at=datetime.utcnow(),
        received_at=datetime.utcnow(),
        exception_class="KeyError",
        exception_message=msg,
    )


async def test_upsert_creates_new_group(async_session: AsyncSession):
    """신규 fingerprint → INSERT, is_new=True, status=OPEN."""
    proj = await _seed_project(async_session)
    event = _make_event(proj, version_sha="a" * 40)
    async_session.add(event)
    await async_session.flush()

    result = await error_group_service.upsert(
        async_session, project_id=proj.id, fingerprint="fp-1", event=event,
    )
    await async_session.commit()

    assert result.is_new is True
    assert result.transitioned_to_regression is False
    assert result.group.status == ErrorGroupStatus.OPEN
    assert result.group.fingerprint == "fp-1"
    assert result.group.event_count == 1
    assert result.group.first_seen_version_sha == "a" * 40
    assert result.group.last_seen_version_sha == "a" * 40


async def test_upsert_updates_existing_open_group(async_session: AsyncSession):
    """기존 OPEN → event_count++, last_seen 갱신, status 그대로."""
    proj = await _seed_project(async_session)
    event1 = _make_event(proj, version_sha="a" * 40)
    async_session.add(event1)
    await async_session.flush()
    await error_group_service.upsert(
        async_session, project_id=proj.id, fingerprint="fp-1", event=event1,
    )
    await async_session.commit()

    event2 = _make_event(proj, version_sha="b" * 40, msg="boom2")
    async_session.add(event2)
    await async_session.flush()
    result = await error_group_service.upsert(
        async_session, project_id=proj.id, fingerprint="fp-1", event=event2,
    )
    await async_session.commit()

    assert result.is_new is False
    assert result.transitioned_to_regression is False
    assert result.group.status == ErrorGroupStatus.OPEN
    assert result.group.event_count == 2
    assert result.group.last_seen_version_sha == "b" * 40
    assert result.group.first_seen_version_sha == "a" * 40
    assert result.group.exception_message_sample == "boom2"


async def test_upsert_transitions_resolved_to_regressed(async_session: AsyncSession):
    """기존 RESOLVED → REGRESSED 전이, transitioned=True."""
    proj = await _seed_project(async_session)
    group = ErrorGroup(
        project_id=proj.id, fingerprint="fp-1",
        exception_class="KeyError", exception_message_sample="old",
        first_seen_at=datetime.utcnow(), first_seen_version_sha="a" * 40,
        last_seen_at=datetime.utcnow(), last_seen_version_sha="a" * 40,
        event_count=5, status=ErrorGroupStatus.RESOLVED,
        resolved_at=datetime.utcnow(),
    )
    async_session.add(group)
    await async_session.commit()

    event = _make_event(proj, version_sha="c" * 40, msg="reopened")
    async_session.add(event)
    await async_session.flush()
    result = await error_group_service.upsert(
        async_session, project_id=proj.id, fingerprint="fp-1", event=event,
    )
    await async_session.commit()

    assert result.is_new is False
    assert result.transitioned_to_regression is True
    assert result.group.status == ErrorGroupStatus.REGRESSED
    assert result.group.event_count == 6


async def test_upsert_ignored_stays_ignored(async_session: AsyncSession):
    """기존 IGNORED → status 그대로, event_count++."""
    proj = await _seed_project(async_session)
    group = ErrorGroup(
        project_id=proj.id, fingerprint="fp-1",
        exception_class="KeyError", exception_message_sample="old",
        first_seen_at=datetime.utcnow(), first_seen_version_sha="a" * 40,
        last_seen_at=datetime.utcnow(), last_seen_version_sha="a" * 40,
        event_count=3, status=ErrorGroupStatus.IGNORED,
    )
    async_session.add(group)
    await async_session.commit()

    event = _make_event(proj, version_sha="d" * 40)
    async_session.add(event)
    await async_session.flush()
    result = await error_group_service.upsert(
        async_session, project_id=proj.id, fingerprint="fp-1", event=event,
    )
    await async_session.commit()

    assert result.is_new is False
    assert result.transitioned_to_regression is False
    assert result.group.status == ErrorGroupStatus.IGNORED
    assert result.group.event_count == 4


async def test_upsert_unique_conflict_falls_back_to_update(async_session: AsyncSession):
    """동일 session 에서 같은 fingerprint 재호출 → SELECT 가 기존 group 발견, UPDATE 분기.

    UNIQUE conflict 의 진정한 race 검증은 다음 테스트 (두 별도 session).
    """
    proj = await _seed_project(async_session)

    event1 = _make_event(proj, version_sha="a" * 40)
    async_session.add(event1)
    await async_session.flush()
    await error_group_service.upsert(
        async_session, project_id=proj.id, fingerprint="fp-race", event=event1,
    )
    await async_session.commit()

    event2 = _make_event(proj, version_sha="b" * 40)
    async_session.add(event2)
    await async_session.flush()
    result = await error_group_service.upsert(
        async_session, project_id=proj.id, fingerprint="fp-race", event=event2,
    )
    await async_session.commit()

    assert result.is_new is False
    assert result.group.event_count == 2


async def test_upsert_concurrent_with_for_update_serializes(
    async_session: AsyncSession, upgraded_db,
):
    """같은 group 의 동시 UPDATE — with_for_update 직렬화 (B1 패턴, 두 session).

    asyncio.Event 로 T1 의 lock 보유 동안 T2 진입 강제.
    """
    proj = await _seed_project(async_session)
    group = ErrorGroup(
        project_id=proj.id, fingerprint="fp-conc",
        exception_class="KeyError", exception_message_sample="x",
        first_seen_at=datetime.utcnow(), first_seen_version_sha="a" * 40,
        last_seen_at=datetime.utcnow(), last_seen_version_sha="a" * 40,
        event_count=0, status=ErrorGroupStatus.OPEN,
    )
    async_session.add(group)
    await async_session.commit()
    project_id = proj.id

    dsn = upgraded_db["async_url"]
    engine_a = create_async_engine(dsn, echo=False)
    engine_b = create_async_engine(dsn, echo=False)
    maker_a = async_sessionmaker(engine_a, expire_on_commit=False)
    maker_b = async_sessionmaker(engine_b, expire_on_commit=False)

    inside_a = asyncio.Event()
    release = asyncio.Event()

    async def runner_t1():
        async with maker_a() as db:
            event = _make_event(proj, version_sha="a" * 40)
            db.add(event)
            await db.flush()
            stmt = (
                select(ErrorGroup)
                .where(ErrorGroup.project_id == project_id, ErrorGroup.fingerprint == "fp-conc")
                .with_for_update()
            )
            grp = (await db.execute(stmt)).scalar_one()
            grp.event_count += 1
            inside_a.set()
            await release.wait()  # T1 lock 보유 시뮬
            await db.commit()

    async def runner_t2():
        await inside_a.wait()
        await asyncio.sleep(0.05)  # T2 lock 대기 진입 보장
        async with maker_b() as db:
            event = _make_event(proj, version_sha="b" * 40)
            db.add(event)
            await db.flush()
            await error_group_service.upsert(
                db, project_id=project_id, fingerprint="fp-conc", event=event,
            )
            await db.commit()

    async def releaser():
        await inside_a.wait()
        await asyncio.sleep(0.3)
        release.set()

    try:
        await asyncio.gather(runner_t1(), runner_t2(), releaser())
    finally:
        await engine_a.dispose()
        await engine_b.dispose()

    await async_session.refresh(group)
    assert group.event_count == 2  # T1's manual +1 + T2's upsert +1
