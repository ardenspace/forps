"""git_repo_service — GitHub Contents API + Compare API 단위 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §5.1 (②), §7.1
"""

import base64

import httpx
import pytest

from app.services.git_repo_service import fetch_file


_REPO = "https://github.com/ardenspace/app-chak"
_SHA = "a" * 40
_PATH = "PLAN.md"


def _mock_contents_response(content: str, status: int = 200) -> httpx.Response:
    if status == 404:
        return httpx.Response(status_code=404, json={"message": "Not Found"})
    body = {
        "name": "PLAN.md",
        "path": "PLAN.md",
        "sha": _SHA,
        "size": len(content),
        "encoding": "base64",
        "content": base64.b64encode(content.encode()).decode(),
    }
    return httpx.Response(status_code=status, json=body)


async def test_fetch_file_decodes_base64_content(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    async def fake_send(self, request: httpx.Request, **_kwargs):
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        return _mock_contents_response("# 스프린트: 테스트\n")

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)
    text = await fetch_file(_REPO, "ghp_abc", _SHA, _PATH)
    assert text == "# 스프린트: 테스트\n"
    assert "/repos/ardenspace/app-chak/contents/PLAN.md" in captured["url"]
    assert f"ref={_SHA}" in captured["url"]
    assert captured["headers"]["authorization"] == "token ghp_abc"


async def test_fetch_file_returns_none_on_404(monkeypatch: pytest.MonkeyPatch):
    async def fake_send(self, request: httpx.Request, **_kwargs):
        return _mock_contents_response("", status=404)

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)
    text = await fetch_file(_REPO, "ghp_abc", _SHA, _PATH)
    assert text is None


async def test_fetch_file_without_pat_omits_authorization(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    async def fake_send(self, request: httpx.Request, **_kwargs):
        captured["headers"] = dict(request.headers)
        return _mock_contents_response("ok")

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)
    await fetch_file(_REPO, None, _SHA, _PATH)
    assert "authorization" not in {k.lower() for k in captured["headers"]}


async def test_fetch_file_5xx_raises(monkeypatch: pytest.MonkeyPatch):
    async def fake_send(self, request: httpx.Request, **_kwargs):
        return httpx.Response(status_code=502, json={"message": "Bad Gateway"})

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_file(_REPO, "ghp_abc", _SHA, _PATH)


async def test_fetch_file_normalizes_repo_url_with_trailing_slash_or_git(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    async def fake_send(self, request: httpx.Request, **_kwargs):
        captured["url"] = str(request.url)
        return _mock_contents_response("ok")

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)
    await fetch_file(_REPO + ".git/", None, _SHA, _PATH)
    assert "/repos/ardenspace/app-chak/contents/PLAN.md" in captured["url"]
