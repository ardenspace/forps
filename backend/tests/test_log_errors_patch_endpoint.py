"""PATCH /errors/{group_id} 통합 테스트.

설계서: 2026-04-26-error-log-design.md §4.1, 5.2
"""

import uuid
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
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


async def _seed(
    db: AsyncSession, *, role: WorkspaceRole = WorkspaceRole.OWNER,
    group_status: ErrorGroupStatus = ErrorGroupStatus.OPEN,
) -> tuple[User, Project, ErrorGroup]:
    user = User(
        email=f"u-{uuid.uuid4().hex[:8]}@x", name="u", password_hash="x",
    )
    db.add(user)
    await db.flush()
    ws = Workspace(name="w", slug=f"w-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.flush()
    db.add(ProjectMember(project_id=proj.id, user_id=user.id, role=role))
    now = datetime.utcnow()
    group = ErrorGroup(
        project_id=proj.id, fingerprint="fp",
        exception_class="ValueError", exception_message_sample="x",
        first_seen_at=now, first_seen_version_sha="a" * 40,
        last_seen_at=now, last_seen_version_sha="a" * 40,
        event_count=1, status=group_status,
    )
    db.add(group)
    await db.commit()
    await db.refresh(user)
    await db.refresh(proj)
    await db.refresh(group)
    return user, proj, group


def _auth(user: User) -> dict[str, str]:
    from app.services.auth_service import create_access_token
    tok = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {tok}"}


async def test_patch_resolve_ok(client_with_db, async_session: AsyncSession):
    user, proj, group = await _seed(async_session)
    sha = "f" * 40
    resp = await client_with_db.patch(
        f"/api/v1/projects/{proj.id}/errors/{group.id}",
        json={"action": "resolve", "resolved_in_version_sha": sha},
        headers=_auth(user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "resolved"
    assert body["resolved_at"] is not None
    assert body["resolved_in_version_sha"] == sha
    assert body["resolved_by_user_id"] == str(user.id)


async def test_patch_owner_required(client_with_db, async_session: AsyncSession):
    user, proj, group = await _seed(async_session, role=WorkspaceRole.EDITOR)
    resp = await client_with_db.patch(
        f"/api/v1/projects/{proj.id}/errors/{group.id}",
        json={"action": "resolve"},
        headers=_auth(user),
    )
    assert resp.status_code == 403


async def test_patch_non_member_404(client_with_db, async_session: AsyncSession):
    user, proj, group = await _seed(async_session)
    # 다른 user — proj 멤버 아님
    other = User(email="other@x", name="o", password_hash="x")
    async_session.add(other)
    await async_session.commit()
    await async_session.refresh(other)

    resp = await client_with_db.patch(
        f"/api/v1/projects/{proj.id}/errors/{group.id}",
        json={"action": "resolve"},
        headers=_auth(other),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


async def test_patch_illegal_transition_400(client_with_db, async_session: AsyncSession):
    user, proj, group = await _seed(async_session, group_status=ErrorGroupStatus.RESOLVED)
    resp = await client_with_db.patch(
        f"/api/v1/projects/{proj.id}/errors/{group.id}",
        json={"action": "ignore"},  # RESOLVED → IGNORED 직접 전이 X
        headers=_auth(user),
    )
    assert resp.status_code == 400
    assert "illegal transition" in resp.json()["detail"].lower()


async def test_patch_unknown_action_422(client_with_db, async_session: AsyncSession):
    user, proj, group = await _seed(async_session)
    resp = await client_with_db.patch(
        f"/api/v1/projects/{proj.id}/errors/{group.id}",
        json={"action": "delete"},
        headers=_auth(user),
    )
    assert resp.status_code == 422  # Pydantic Literal 검증


async def test_patch_extra_field_rejected(client_with_db, async_session: AsyncSession):
    user, proj, group = await _seed(async_session)
    resp = await client_with_db.patch(
        f"/api/v1/projects/{proj.id}/errors/{group.id}",
        json={"action": "resolve", "status": "resolved"},  # extra='forbid'
        headers=_auth(user),
    )
    assert resp.status_code == 422


async def test_patch_group_not_in_project_404(client_with_db, async_session: AsyncSession):
    user, proj, group = await _seed(async_session)
    # 다른 project 의 group_id 로 PATCH 시도
    other_proj = Project(workspace_id=proj.workspace_id, name="other")
    async_session.add(other_proj)
    await async_session.commit()
    await async_session.refresh(other_proj)
    async_session.add(ProjectMember(
        project_id=other_proj.id, user_id=user.id, role=WorkspaceRole.OWNER,
    ))
    await async_session.commit()

    resp = await client_with_db.patch(
        f"/api/v1/projects/{other_proj.id}/errors/{group.id}",  # group 은 첫 proj
        json={"action": "resolve"},
        headers=_auth(user),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Error group not found"
