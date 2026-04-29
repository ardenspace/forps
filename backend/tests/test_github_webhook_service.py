"""github_webhook_service — 서명 검증 / repo 매칭 / GitPushEvent INSERT 단위 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §10.2
"""

import hashlib
import hmac
import json
from pathlib import Path

import pytest

from app.services.github_webhook_service import verify_signature


FIXTURE = (Path(__file__).parent / "fixtures" / "github_push_payload.json").read_bytes()


def _sign(body: bytes, secret: str) -> str:
    """`X-Hub-Signature-256` 형식과 동일하게 HMAC-SHA256 생성."""
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def test_verify_signature_pass():
    secret = "the-shared-webhook-secret"
    sig = _sign(FIXTURE, secret)
    assert verify_signature(FIXTURE, sig, secret) is True


def test_verify_signature_fail_wrong_secret():
    sig = _sign(FIXTURE, "the-real-secret")
    assert verify_signature(FIXTURE, sig, "different-secret") is False


def test_verify_signature_fail_tampered_body():
    secret = "the-shared-webhook-secret"
    sig = _sign(FIXTURE, secret)
    tampered = FIXTURE + b"x"
    assert verify_signature(tampered, sig, secret) is False


def test_verify_signature_missing_prefix():
    """`sha256=` prefix 없으면 reject."""
    secret = "the-shared-webhook-secret"
    mac = hmac.new(secret.encode(), FIXTURE, hashlib.sha256).hexdigest()
    assert verify_signature(FIXTURE, mac, secret) is False  # prefix 빠짐


def test_verify_signature_empty_signature():
    assert verify_signature(FIXTURE, "", "secret") is False
    assert verify_signature(FIXTURE, None, "secret") is False  # type: ignore[arg-type]


import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.workspace import Workspace
from app.services.github_webhook_service import find_project_by_repo_url


async def _seed_workspace_with_project(
    db: AsyncSession, repo_url: str | None
) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p", git_repo_url=repo_url)
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def test_find_project_exact_match(async_session: AsyncSession):
    proj = await _seed_workspace_with_project(
        async_session, "https://github.com/ardenspace/app-chak"
    )
    found = await find_project_by_repo_url(
        async_session, "https://github.com/ardenspace/app-chak"
    )
    assert found is not None
    assert found.id == proj.id


async def test_find_project_normalizes_trailing_slash_and_git_suffix(
    async_session: AsyncSession,
):
    """webhook payload 의 html_url vs clone_url 차이 흡수.

    Project 측에 `https://github.com/foo/bar` 만 들어있어도 webhook 의 `.../bar.git` 매칭.
    """
    proj = await _seed_workspace_with_project(
        async_session, "https://github.com/ardenspace/app-chak"
    )
    for variant in [
        "https://github.com/ardenspace/app-chak.git",
        "https://github.com/ardenspace/app-chak/",
        "HTTPS://GitHub.com/ardenspace/app-chak",
    ]:
        found = await find_project_by_repo_url(async_session, variant)
        assert found is not None and found.id == proj.id, f"variant {variant} mismatch"


async def test_find_project_unknown_repo_returns_none(async_session: AsyncSession):
    await _seed_workspace_with_project(async_session, "https://github.com/a/known")
    found = await find_project_by_repo_url(async_session, "https://github.com/x/y")
    assert found is None


async def test_find_project_skips_null_git_repo_url(async_session: AsyncSession):
    """git_repo_url이 None인 Project는 매칭 후보에서 제외."""
    await _seed_workspace_with_project(async_session, None)
    found = await find_project_by_repo_url(async_session, "https://github.com/x/y")
    assert found is None
