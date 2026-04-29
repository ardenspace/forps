"""POST /api/v1/webhooks/github e2e 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §7.1, §8 (응답 정책)
- 401: 서명 검증 실패
- 200 + 경고 로그: 알 수 없는 repo (GitHub 재전송 방지)
- 200: 정상 + GitPushEvent INSERT
- 200: 중복 commit_sha (멱등성)
"""

import hashlib
import hmac
import json
import uuid
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret
from app.models.git_push_event import GitPushEvent
from app.models.project import Project
from app.models.workspace import Workspace


FIXTURE = (Path(__file__).parent / "fixtures" / "github_push_payload.json").read_bytes()


@pytest.fixture()
async def client_with_db(async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    """FORPS_FERNET_KEY + DB override 적용한 ASGI 클라이언트."""
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


async def _seed_project_with_secret(
    db: AsyncSession, repo_url: str, secret: str | None
) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(
        workspace_id=ws.id,
        name="p",
        git_repo_url=repo_url,
        webhook_secret_encrypted=encrypt_secret(secret) if secret else None,
    )
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


def _sign(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


async def test_webhook_valid_signature_returns_200(
    client_with_db, async_session: AsyncSession
):
    secret = "valid-secret"
    proj = await _seed_project_with_secret(
        async_session, "https://github.com/ardenspace/app-chak", secret
    )
    sig = _sign(FIXTURE, secret)
    res = await client_with_db.post(
        "/api/v1/webhooks/github",
        content=FIXTURE,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )
    assert res.status_code == 200

    rows = (
        await async_session.execute(
            select(GitPushEvent).where(GitPushEvent.project_id == proj.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].head_commit_sha == json.loads(FIXTURE)["head_commit"]["id"]


async def test_webhook_invalid_signature_returns_401(
    client_with_db, async_session: AsyncSession
):
    proj = await _seed_project_with_secret(
        async_session, "https://github.com/ardenspace/app-chak", "real-secret"
    )
    bad_sig = _sign(FIXTURE, "wrong-secret")
    res = await client_with_db.post(
        "/api/v1/webhooks/github",
        content=FIXTURE,
        headers={"X-Hub-Signature-256": bad_sig, "X-GitHub-Event": "push"},
    )
    assert res.status_code == 401

    # body 미저장 — DB row 없어야
    rows = (
        await async_session.execute(
            select(GitPushEvent).where(GitPushEvent.project_id == proj.id)
        )
    ).scalars().all()
    assert len(rows) == 0


async def test_webhook_unknown_repo_returns_200(
    client_with_db, async_session: AsyncSession
):
    """알 수 없는 repo: 200 + 경고 로그 (GitHub 재전송 방지)."""
    # 다른 repo URL의 Project 만 있음
    await _seed_project_with_secret(
        async_session, "https://github.com/other/repo", "secret"
    )
    res = await client_with_db.post(
        "/api/v1/webhooks/github",
        content=FIXTURE,
        headers={"X-Hub-Signature-256": "sha256=anything", "X-GitHub-Event": "push"},
    )
    assert res.status_code == 200

    rows = (await async_session.execute(select(GitPushEvent))).scalars().all()
    assert len(rows) == 0


async def test_webhook_missing_signature_returns_401(
    client_with_db, async_session: AsyncSession
):
    await _seed_project_with_secret(
        async_session, "https://github.com/ardenspace/app-chak", "secret"
    )
    res = await client_with_db.post(
        "/api/v1/webhooks/github",
        content=FIXTURE,
        headers={"X-GitHub-Event": "push"},
    )
    assert res.status_code == 401


async def test_webhook_duplicate_push_idempotent(
    client_with_db, async_session: AsyncSession
):
    secret = "valid-secret"
    proj = await _seed_project_with_secret(
        async_session, "https://github.com/ardenspace/app-chak", secret
    )
    sig = _sign(FIXTURE, secret)
    headers = {"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"}

    res1 = await client_with_db.post(
        "/api/v1/webhooks/github", content=FIXTURE, headers=headers
    )
    res2 = await client_with_db.post(
        "/api/v1/webhooks/github", content=FIXTURE, headers=headers
    )
    assert res1.status_code == 200
    assert res2.status_code == 200

    rows = (
        await async_session.execute(
            select(GitPushEvent).where(GitPushEvent.project_id == proj.id)
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_webhook_project_without_secret_returns_401(
    client_with_db, async_session: AsyncSession
):
    """git_repo_url은 매칭되지만 webhook_secret_encrypted 가 NULL → 401."""
    await _seed_project_with_secret(
        async_session, "https://github.com/ardenspace/app-chak", secret=None
    )
    res = await client_with_db.post(
        "/api/v1/webhooks/github",
        content=FIXTURE,
        headers={"X-Hub-Signature-256": "sha256=x", "X-GitHub-Event": "push"},
    )
    assert res.status_code == 401
