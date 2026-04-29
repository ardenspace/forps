"""Phase 4 마이그레이션 회귀 — github_pat_encrypted 컬럼 추가가 기존 Project 데이터를 보존하는지 검증."""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.workspace import Workspace


async def test_existing_projects_have_null_github_pat_after_migration(
    async_session: AsyncSession,
):
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(workspace_id=ws.id, name="legacy")
    async_session.add(proj)
    await async_session.commit()
    await async_session.refresh(proj)

    assert proj.github_pat_encrypted is None  # 기본값 NULL


async def test_github_pat_round_trip(async_session: AsyncSession):
    """Fernet 암호화된 bytes 가 LargeBinary 컬럼에 저장/조회 가능."""
    from app.core.crypto import decrypt_secret, encrypt_secret

    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(
        workspace_id=ws.id,
        name="with_pat",
        github_pat_encrypted=encrypt_secret("ghp_abcd1234"),
    )
    async_session.add(proj)
    await async_session.commit()
    await async_session.refresh(proj)

    assert proj.github_pat_encrypted is not None
    assert decrypt_secret(proj.github_pat_encrypted) == "ghp_abcd1234"


async def test_migration_added_column_to_projects_table(async_session: AsyncSession):
    """conftest 의 testcontainer 가 head 까지 마이그레이션 적용 — 컬럼 존재 자체 확인."""
    result = await async_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'projects' AND column_name = 'github_pat_encrypted'"
        )
    )
    row = result.first()
    assert row is not None
    assert row[0] == "github_pat_encrypted"
