"""log_health_service.compute_health 단위 테스트."""

import uuid
from datetime import datetime, timedelta, date

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_event import LogEvent, LogLevel
from app.models.project import Project
from app.models.workspace import Workspace
from app.services import log_health_service


async def _seed_project(db: AsyncSession) -> Project:
    ws = Workspace(name="w", slug=f"w-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


def _evt(
    proj_id, *, version_sha: str = "a" * 40, level: LogLevel = LogLevel.INFO,
    emitted_offset_minutes: float = 0.0, received_offset_minutes: float = 0.0,
) -> LogEvent:
    """현재 시각 기준 received_at, emitted_at 을 분 단위 offset 으로 조정."""
    now = datetime.utcnow()
    return LogEvent(
        project_id=proj_id,
        level=level, message="x", logger_name="l",
        version_sha=version_sha, environment="prod", hostname="h",
        emitted_at=now + timedelta(minutes=emitted_offset_minutes),
        received_at=now + timedelta(minutes=received_offset_minutes),
    )


async def test_compute_health_empty(async_session: AsyncSession):
    proj = await _seed_project(async_session)
    health = await log_health_service.compute_health(async_session, project_id=proj.id)
    assert health["total_events_24h"] == 0
    assert health["unknown_sha_count_24h"] == 0
    assert health["unknown_sha_ratio_24h"] == 0.0
    assert health["clock_drift_count_24h"] == 0


async def test_compute_health_unknown_ratio(async_session: AsyncSession):
    proj = await _seed_project(async_session)
    # 4 known + 1 unknown = 20% ratio
    for _ in range(4):
        async_session.add(_evt(proj.id, version_sha="a" * 40))
    async_session.add(_evt(proj.id, version_sha="unknown"))
    await async_session.commit()

    health = await log_health_service.compute_health(async_session, project_id=proj.id)
    assert health["total_events_24h"] == 5
    assert health["unknown_sha_count_24h"] == 1
    assert abs(health["unknown_sha_ratio_24h"] - 0.2) < 1e-9


async def test_compute_health_clock_drift(async_session: AsyncSession):
    proj = await _seed_project(async_session)
    # 1 정상 + 1 시계 어긋남 (received - emitted = 90분)
    async_session.add(_evt(proj.id, emitted_offset_minutes=0, received_offset_minutes=0))
    async_session.add(_evt(proj.id, emitted_offset_minutes=-90, received_offset_minutes=0))
    await async_session.commit()

    health = await log_health_service.compute_health(async_session, project_id=proj.id)
    assert health["total_events_24h"] == 2
    assert health["clock_drift_count_24h"] == 1


async def test_compute_health_excludes_old(async_session: AsyncSession):
    """24h 보다 오래된 이벤트는 카운트 제외.

    log_events 는 received_at 기준 daily range partition. 마이그레이션은
    today~+30일 파티션만 생성 — yesterday 파티션이 없으므로 테스트 안에서
    직접 CREATE PARTITION 후 25h-old 이벤트를 삽입.
    """
    proj = await _seed_project(async_session)

    # yesterday 파티션 수동 생성 (마이그레이션은 오늘부터 +30일만 생성)
    yesterday = date.today() - timedelta(days=1)
    today = date.today()
    partition_name = f"log_events_{yesterday.strftime('%Y%m%d')}"
    await async_session.execute(text(
        f"CREATE TABLE IF NOT EXISTS {partition_name} "
        f"PARTITION OF log_events "
        f"FOR VALUES FROM ('{yesterday.isoformat()}') TO ('{today.isoformat()}')"
    ))
    await async_session.commit()

    # 25h 전 (yesterday 파티션) — 제외
    async_session.add(_evt(proj.id, emitted_offset_minutes=-25*60, received_offset_minutes=-25*60))
    # 1h 전 (today 파티션) — 포함
    async_session.add(_evt(proj.id, emitted_offset_minutes=-60, received_offset_minutes=-60))
    await async_session.commit()

    health = await log_health_service.compute_health(async_session, project_id=proj.id)
    assert health["total_events_24h"] == 1


async def test_compute_health_isolated_per_project(async_session: AsyncSession):
    """다른 프로젝트의 이벤트는 카운트 안 함."""
    proj_a = await _seed_project(async_session)
    proj_b = await _seed_project(async_session)
    async_session.add(_evt(proj_a.id))
    async_session.add(_evt(proj_b.id, version_sha="unknown"))
    async_session.add(_evt(proj_b.id, version_sha="unknown"))
    await async_session.commit()

    health_a = await log_health_service.compute_health(async_session, project_id=proj_a.id)
    health_b = await log_health_service.compute_health(async_session, project_id=proj_b.id)
    assert health_a["total_events_24h"] == 1
    assert health_a["unknown_sha_count_24h"] == 0
    assert health_b["total_events_24h"] == 2
    assert health_b["unknown_sha_count_24h"] == 2
