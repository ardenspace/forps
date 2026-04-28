import pytest
import psycopg
from sqlalchemy import text


def test_pytest_works():
    """Trivial assertion — verifies pytest is wired up."""
    assert 1 + 1 == 2


def test_alembic_upgrade_head(upgraded_db):
    """Verify that alembic upgrade head creates the expected pre-Phase-1 tables."""
    expected_tables = {"users", "projects", "tasks", "alembic_version"}

    sync_url = upgraded_db["sync_url"].replace("postgresql+psycopg://", "postgresql://")

    with psycopg.connect(sync_url) as conn:
        rows = conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall()

    actual_tables = {row[0] for row in rows}

    missing = expected_tables - actual_tables
    assert not missing, f"Missing tables after upgrade head: {missing}"


@pytest.mark.asyncio
async def test_async_session(async_session):
    """Verify async SQLAlchemy session works against the migrated DB."""
    result = await async_session.execute(text("SELECT 1"))
    value = result.scalar()
    assert value == 1
