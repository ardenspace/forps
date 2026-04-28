"""CHECK / UNIQUE 제약 동작 — 설계서 Decision Log Rev3 의 sha 형식 강제."""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_handoff_short_sha_rejected(async_session):
    """handoffs.commit_sha 가 40자 hex 가 아니면 reject."""
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    await async_session.execute(text(
        "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
        "VALUES (:id, 'w', 's1', now(), now())"
    ), {"id": workspace_id})
    await async_session.execute(text(
        "INSERT INTO users(id, email, name, password_hash, created_at, updated_at) "
        "VALUES (:id, 'u@x.com', 'u', 'h', now(), now())"
    ), {"id": user_id})
    await async_session.execute(text(
        "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
        "VALUES (:id, :ws, 'p', now(), now())"
    ), {"id": project_id, "ws": workspace_id})
    await async_session.commit()

    with pytest.raises(IntegrityError):
        await async_session.execute(text(
            "INSERT INTO handoffs(id, project_id, branch, author_git_login, "
            "commit_sha, pushed_at, created_at) "
            "VALUES (:id, :pid, 'main', 'a', 'abc', now(), now())"
        ), {"id": uuid.uuid4(), "pid": project_id})
        await async_session.commit()


@pytest.mark.asyncio
async def test_handoff_full_sha_accepted(async_session):
    """40자 hex 는 통과."""
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    await async_session.execute(text(
        "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
        "VALUES (:id, 'w', 's2', now(), now())"
    ), {"id": workspace_id})
    await async_session.execute(text(
        "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
        "VALUES (:id, :ws, 'p', now(), now())"
    ), {"id": project_id, "ws": workspace_id})
    await async_session.commit()

    full = "a" * 40
    await async_session.execute(text(
        "INSERT INTO handoffs(id, project_id, branch, author_git_login, "
        "commit_sha, pushed_at, created_at) "
        "VALUES (:id, :pid, 'main', 'a', :sha, now(), now())"
    ), {"id": uuid.uuid4(), "pid": project_id, "sha": full})
    await async_session.commit()


@pytest.mark.asyncio
async def test_log_event_unknown_version_sha_accepted(async_session):
    """LogEvent.version_sha = 'unknown' 은 허용."""
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    await async_session.execute(text(
        "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
        "VALUES (:id, 'w', 's3', now(), now())"
    ), {"id": workspace_id})
    await async_session.execute(text(
        "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
        "VALUES (:id, :ws, 'p', now(), now())"
    ), {"id": project_id, "ws": workspace_id})
    await async_session.commit()

    await async_session.execute(text(
        "INSERT INTO log_events(id, project_id, level, message, logger_name, "
        "version_sha, environment, hostname, emitted_at, received_at) "
        "VALUES (:id, :pid, 'INFO', 'm', 'l', 'unknown', 'dev', 'h', now(), now())"
    ), {"id": uuid.uuid4(), "pid": project_id})
    await async_session.commit()


@pytest.mark.asyncio
async def test_log_event_short_version_sha_rejected(async_session):
    """7자 short SHA 는 reject (Rev3 Decision)."""
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    await async_session.execute(text(
        "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
        "VALUES (:id, 'w', 's4', now(), now())"
    ), {"id": workspace_id})
    await async_session.execute(text(
        "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
        "VALUES (:id, :ws, 'p', now(), now())"
    ), {"id": project_id, "ws": workspace_id})
    await async_session.commit()

    with pytest.raises(IntegrityError):
        await async_session.execute(text(
            "INSERT INTO log_events(id, project_id, level, message, logger_name, "
            "version_sha, environment, hostname, emitted_at, received_at) "
            "VALUES (:id, :pid, 'INFO', 'm', 'l', 'abc1234', 'dev', 'h', now(), now())"
        ), {"id": uuid.uuid4(), "pid": project_id})
        await async_session.commit()


@pytest.mark.asyncio
async def test_task_external_id_unique_per_project(async_session):
    """external_id 같은 값 같은 project → reject. NULL 은 다중 허용."""
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    await async_session.execute(text(
        "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
        "VALUES (:id, 'w', 's5', now(), now())"
    ), {"id": workspace_id})
    await async_session.execute(text(
        "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
        "VALUES (:id, :ws, 'p', now(), now())"
    ), {"id": project_id, "ws": workspace_id})

    # NULL 두 개 — 통과
    await async_session.execute(text(
        "INSERT INTO tasks(id, project_id, title, status, source, created_at, updated_at) "
        "VALUES (:id, :pid, 't1', 'TODO'::taskstatus, 'MANUAL', now(), now())"
    ), {"id": uuid.uuid4(), "pid": project_id})
    await async_session.execute(text(
        "INSERT INTO tasks(id, project_id, title, status, source, created_at, updated_at) "
        "VALUES (:id, :pid, 't2', 'TODO'::taskstatus, 'MANUAL', now(), now())"
    ), {"id": uuid.uuid4(), "pid": project_id})
    await async_session.commit()

    # 같은 external_id "task-001" 두 개 → reject
    await async_session.execute(text(
        "INSERT INTO tasks(id, project_id, title, status, source, external_id, created_at, updated_at) "
        "VALUES (:id, :pid, 't3', 'TODO'::taskstatus, 'MANUAL', 'task-001', now(), now())"
    ), {"id": uuid.uuid4(), "pid": project_id})
    await async_session.commit()

    with pytest.raises(IntegrityError):
        await async_session.execute(text(
            "INSERT INTO tasks(id, project_id, title, status, source, external_id, created_at, updated_at) "
            "VALUES (:id, :pid, 't4', 'TODO'::taskstatus, 'MANUAL', 'task-001', now(), now())"
        ), {"id": uuid.uuid4(), "pid": project_id})
        await async_session.commit()


@pytest.mark.asyncio
async def test_handoff_unique_project_commit(async_session):
    """webhook 재전송 멱등성: 같은 (project_id, commit_sha) → reject."""
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    await async_session.execute(text(
        "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
        "VALUES (:id, 'w', 's6', now(), now())"
    ), {"id": workspace_id})
    await async_session.execute(text(
        "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
        "VALUES (:id, :ws, 'p', now(), now())"
    ), {"id": project_id, "ws": workspace_id})
    await async_session.commit()

    sha = "b" * 40
    await async_session.execute(text(
        "INSERT INTO handoffs(id, project_id, branch, author_git_login, "
        "commit_sha, pushed_at, created_at) "
        "VALUES (:id, :pid, 'main', 'a', :sha, now(), now())"
    ), {"id": uuid.uuid4(), "pid": project_id, "sha": sha})
    await async_session.commit()

    with pytest.raises(IntegrityError):
        await async_session.execute(text(
            "INSERT INTO handoffs(id, project_id, branch, author_git_login, "
            "commit_sha, pushed_at, created_at) "
            "VALUES (:id, :pid, 'feat', 'b', :sha, now(), now())"
        ), {"id": uuid.uuid4(), "pid": project_id, "sha": sha})
        await async_session.commit()


@pytest.mark.asyncio
async def test_orm_roundtrip_with_phase1_enum(async_session):
    """ORM INSERT/SELECT 가 Phase 1 enum 매핑 정확.

    SQLAlchemy enum default = NAME (대문자) 사용. DB enum 도 대문자.
    Python enum 의 .value 가 소문자여도 ORM 매핑 시 NAME 으로 직렬화/역직렬화.
    """
    from app.models.task import Task, TaskSource
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    await async_session.execute(text(
        "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
        "VALUES (:id, 'w', 'sorm', now(), now())"
    ), {"id": workspace_id})
    await async_session.execute(text(
        "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
        "VALUES (:id, :ws, 'p', now(), now())"
    ), {"id": project_id, "ws": workspace_id})
    await async_session.commit()

    task = Task(
        project_id=project_id,
        title="orm-roundtrip",
        source=TaskSource.SYNCED_FROM_PLAN,
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)

    assert task.source == TaskSource.SYNCED_FROM_PLAN, (
        f"ORM round-trip 실패: source={task.source!r}"
    )
