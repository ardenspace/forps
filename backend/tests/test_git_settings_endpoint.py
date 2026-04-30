"""git-settings endpoint e2e 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §5.2, §9
"""

import uuid

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceRole


@pytest.fixture()
async def client_with_db(async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FORPS_FERNET_KEY", Fernet.generate_key().decode())
    import importlib
    import app.config
    importlib.reload(app.config)
    import app.core.crypto
    importlib.reload(app.core.crypto)

    from app.main import app
    from app.database import get_db

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _seed_user_project(
    db: AsyncSession,
    role: WorkspaceRole = WorkspaceRole.OWNER,
) -> tuple[User, Project]:
    user = User(
        email=f"u-{uuid.uuid4().hex[:8]}@example.com",
        name="alice",
        password_hash="x",
    )
    db.add(user)
    await db.flush()
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.flush()
    db.add(ProjectMember(project_id=proj.id, user_id=user.id, role=role))
    await db.commit()
    await db.refresh(user)
    await db.refresh(proj)
    return user, proj


def _auth_token(user: User) -> str:
    from app.services.auth_service import create_access_token

    return create_access_token({"sub": str(user.id)})


async def test_get_git_settings_returns_current_state(
    client_with_db, async_session: AsyncSession
):
    user, proj = await _seed_user_project(async_session)
    token = _auth_token(user)
    res = await client_with_db.get(
        f"/api/v1/projects/{proj.id}/git-settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["git_repo_url"] is None
    assert body["plan_path"] == "PLAN.md"
    assert body["handoff_dir"] == "handoffs/"
    assert body["has_webhook_secret"] is False
    assert body["has_github_pat"] is False
    assert "public_webhook_url" in body


async def test_get_git_settings_404_for_non_member(
    client_with_db, async_session: AsyncSession
):
    user, proj = await _seed_user_project(async_session)

    other = User(
        email=f"o-{uuid.uuid4().hex[:8]}@example.com",
        name="bob",
        password_hash="x",
    )
    async_session.add(other)
    await async_session.commit()
    await async_session.refresh(other)

    token = _auth_token(other)
    res = await client_with_db.get(
        f"/api/v1/projects/{proj.id}/git-settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


async def test_get_git_settings_redacts_secrets(
    client_with_db, async_session: AsyncSession
):
    user, proj = await _seed_user_project(async_session)
    proj.github_pat_encrypted = encrypt_secret("ghp_super_secret_token")
    proj.webhook_secret_encrypted = encrypt_secret("super-shared-secret")
    await async_session.commit()
    await async_session.refresh(proj)

    token = _auth_token(user)
    res = await client_with_db.get(
        f"/api/v1/projects/{proj.id}/git-settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["has_github_pat"] is True
    assert body["has_webhook_secret"] is True
    assert "github_pat" not in body
    assert "github_pat_encrypted" not in body
    assert "webhook_secret" not in body
    assert "webhook_secret_encrypted" not in body
    raw_text = res.text
    assert "ghp_super_secret_token" not in raw_text
    assert "super-shared-secret" not in raw_text
