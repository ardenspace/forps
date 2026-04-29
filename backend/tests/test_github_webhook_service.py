"""github_webhook_service — 서명 검증 / repo 매칭 / GitPushEvent INSERT 단위 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §10.2
"""

import hashlib
import hmac
import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_push_event import GitPushEvent
from app.models.project import Project
from app.models.workspace import Workspace
from app.schemas.webhook import GitHubPushPayload
from app.services.github_webhook_service import (
    find_project_by_repo_url,
    record_push_event,
    verify_signature,
)


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


def _payload(commits_count: int = 1, head_id: str | None = None) -> GitHubPushPayload:
    raw = json.loads(FIXTURE.decode())
    one = raw["commits"][0]
    raw["commits"] = [one] * commits_count
    if head_id is not None:
        raw["head_commit"]["id"] = head_id
        raw["after"] = head_id
    return GitHubPushPayload.model_validate(raw)


async def test_record_push_event_inserts_row(async_session: AsyncSession):
    proj = await _seed_workspace_with_project(
        async_session, "https://github.com/ardenspace/app-chak"
    )
    payload = _payload()
    event = await record_push_event(async_session, proj, payload)

    assert event is not None
    assert event.project_id == proj.id
    assert event.head_commit_sha == payload.head_commit.id
    assert event.branch == "feature/login-redesign"
    assert event.pusher == "alice"
    assert event.commits_truncated is False
    assert event.processed_at is None
    assert event.error is None
    assert event.commits is not None and len(event.commits) == 1


async def test_record_push_event_truncated_flag_at_20(async_session: AsyncSession):
    proj = await _seed_workspace_with_project(
        async_session, "https://github.com/ardenspace/app-chak"
    )
    payload = _payload(commits_count=20)
    event = await record_push_event(async_session, proj, payload)
    assert event.commits_truncated is True


async def test_record_push_event_idempotent_on_duplicate_sha(
    async_session: AsyncSession,
):
    """UNIQUE (project_id, head_commit_sha) 충돌 시 silent skip — 같은 객체 또는 None 반환."""
    proj = await _seed_workspace_with_project(
        async_session, "https://github.com/ardenspace/app-chak"
    )
    payload = _payload(head_id="a" * 40)

    first = await record_push_event(async_session, proj, payload)
    assert first is not None

    # 같은 head_commit_sha 로 두 번째 호출
    second = await record_push_event(async_session, proj, payload)
    # 새 row INSERT 안 됨
    rows = (
        await async_session.execute(
            select(GitPushEvent).where(GitPushEvent.project_id == proj.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    # second는 기존 row 반환 또는 None — 둘 다 허용 (silent 의미)
    if second is not None:
        assert second.id == first.id
