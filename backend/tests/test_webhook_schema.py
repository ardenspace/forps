"""GitHub push webhook payload Pydantic 스키마 테스트."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.webhook import GitHubPushPayload


FIXTURE = Path(__file__).parent / "fixtures" / "github_push_payload.json"


def test_parse_valid_payload():
    payload = GitHubPushPayload.model_validate(json.loads(FIXTURE.read_text()))
    assert payload.ref == "refs/heads/feature/login-redesign"
    assert payload.repository.html_url == "https://github.com/ardenspace/app-chak"
    assert payload.head_commit.id == "abcdef0123456789abcdef0123456789abcdef01"
    assert payload.pusher.name == "alice"
    assert len(payload.commits) == 1


def test_branch_property_strips_refs_heads():
    payload = GitHubPushPayload.model_validate(json.loads(FIXTURE.read_text()))
    assert payload.branch == "feature/login-redesign"


def test_head_commit_required():
    data = json.loads(FIXTURE.read_text())
    data.pop("head_commit")
    with pytest.raises(ValidationError):
        GitHubPushPayload.model_validate(data)


def test_commits_truncated_at_20():
    """webhook 은 commits 최대 20개. 본 테스트는 길이 검증 — truncated 플래그 자체는 service 단계."""
    data = json.loads(FIXTURE.read_text())
    one = data["commits"][0]
    data["commits"] = [one] * 25
    payload = GitHubPushPayload.model_validate(data)
    assert len(payload.commits) == 25  # schema는 길이 제한 안 함; service에서 commits_truncated 결정
