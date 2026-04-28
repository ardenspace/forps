"""마이그레이션 회귀 — CRITICAL.

설계서:
- task-automation §10.3: 기존 production-like 데이터셋 위에서 alembic up,
  기존 API 응답이 byte-equal 동일.
- error-log §10.4: 기존 모델 무변경 + alembic up/down 정상.
"""
import uuid
from datetime import datetime

import psycopg
import pytest
from alembic import command

import app.config


def _seed_pre_phase1(conn):
    """Phase 1 직전 상태의 production-like 데이터 시딩."""
    workspace_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO workspaces(id, name, slug, created_at, updated_at) "
            "VALUES (%s, %s, %s, now(), now())",
            (workspace_id, "ws", "ws-slug"),
        )
        cur.execute(
            "INSERT INTO users(id, email, name, password_hash, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, now(), now())",
            (user_id, "u@x.com", "u", "h"),
        )
        cur.execute(
            "INSERT INTO projects(id, workspace_id, name, created_at, updated_at) "
            "VALUES (%s, %s, %s, now(), now())",
            (project_id, workspace_id, "p"),
        )
        cur.execute(
            "INSERT INTO tasks(id, project_id, title, status, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s::taskstatus, now(), now())",
            (task_id, project_id, "기존 태스크", "TODO"),
        )
    conn.commit()
    return {"task_id": task_id, "project_id": project_id, "user_id": user_id}


def _sync_conn_from_config(alembic_config):
    """alembic_config 에서 psycopg (sync) 연결을 만든다.

    env.py 가 URL 을 덮어쓰므로 settings.database_url 에서 직접 읽는다.
    postgresql+asyncpg:// → postgresql:// 변환.
    """
    url = app.config.settings.database_url
    # asyncpg driver prefix 제거
    plain_url = url.replace("+asyncpg", "")
    # postgresql:// 는 psycopg 가 기본으로 처리
    return psycopg.connect(plain_url)


@pytest.fixture()
def patched_alembic_config(alembic_config, postgres_container, fresh_db):
    """alembic_config + settings.database_url 패치.

    env.py 가 module-level 에서 settings.database_url 을 읽어 sqlalchemy.url 을
    덮어쓰므로, command.upgrade/downgrade 전에 settings 를 패치해야 한다.
    upgraded_db fixture 와 동일한 패턴.
    """
    from tests.conftest import _db_dsn_async
    async_url = _db_dsn_async(postgres_container, fresh_db)
    original = app.config.settings.database_url
    app.config.settings.database_url = async_url
    try:
        yield alembic_config
    finally:
        app.config.settings.database_url = original


def test_existing_data_preserved_after_phase1(patched_alembic_config):
    """Phase 1 직전 head 까지 올린 후 데이터 시딩 → Phase 1 적용 → 무손실.

    `upgraded_db` 는 항상 head 까지 올리므로 직접 alembic command 사용.
    """
    cfg = patched_alembic_config
    command.upgrade(cfg, "be8724268ae4")
    conn = _sync_conn_from_config(cfg)
    seeded = _seed_pre_phase1(conn)
    conn.close()

    command.upgrade(cfg, "head")

    conn = _sync_conn_from_config(cfg)
    with conn.cursor() as cur:
        cur.execute("SELECT title, status::text FROM tasks WHERE id = %s", (seeded["task_id"],))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "기존 태스크"
        assert row[1] == "TODO"

        cur.execute(
            "SELECT source::text, external_id, last_commit_sha, archived_at "
            "FROM tasks WHERE id = %s",
            (seeded["task_id"],),
        )
        row = cur.fetchone()
        assert row[0] == "MANUAL", "기존 task 의 source 가 MANUAL default 가 아님"
        assert row[1] is None
        assert row[2] is None
        assert row[3] is None

        cur.execute(
            "SELECT git_default_branch, plan_path, handoff_dir "
            "FROM projects WHERE id = %s",
            (seeded["project_id"],),
        )
        row = cur.fetchone()
        assert row == ("main", "PLAN.md", "handoffs/")
    conn.close()


def test_alembic_downgrade_then_upgrade_roundtrip(patched_alembic_config):
    """upgrade head → downgrade -1 → upgrade head 가 깨끗이 돈다."""
    cfg = patched_alembic_config
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")
    command.upgrade(cfg, "head")


def test_downgrade_drops_phase1_objects(patched_alembic_config):
    """downgrade -1 후 phase1 객체가 모두 사라진다."""
    cfg = patched_alembic_config
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")

    conn = _sync_conn_from_config(cfg)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public'"
        )
        tables = {row[0] for row in cur.fetchall()}
    conn.close()
    for t in [
        "handoffs", "git_push_events", "log_ingest_tokens",
        "rate_limit_windows", "error_groups", "log_events",
    ]:
        assert t not in tables, f"downgrade 후 {t} 가 남아있음"


def test_task_event_action_existing_values_preserved_after_phase1(
    patched_alembic_config,
):
    """ALTER TYPE ADD VALUE 로 기존 enum 값이 사라지면 안 됨."""
    cfg = patched_alembic_config
    command.upgrade(cfg, "head")
    conn = _sync_conn_from_config(cfg)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT enumlabel FROM pg_enum "
            "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
            "WHERE pg_type.typname = 'taskeventaction' "
            "ORDER BY enumlabel"
        )
        labels = {row[0] for row in cur.fetchall()}
    conn.close()
    # 기존 6값은 UPPER_CASE 로 생성되어 있음 (initial migration 참고)
    assert {"CREATED", "UPDATED", "STATUS_CHANGED", "ASSIGNED", "COMMENTED", "DELETED"} <= labels
    # Phase 1 에서 ADD VALUE 한 4값도 UPPER_CASE 로 통일
    assert {"SYNCED_FROM_PLAN", "CHECKED_BY_COMMIT", "UNCHECKED_BY_COMMIT", "ARCHIVED_FROM_PLAN"} <= labels
