"""Handoff 모델 정의 검증 (모델만)."""
from app.models.handoff import Handoff


def test_handoff_fields():
    a = Handoff.__annotations__
    for f in [
        "id", "project_id", "branch", "author_user_id", "author_git_login",
        "commit_sha", "pushed_at", "raw_content", "parsed_tasks", "free_notes",
    ]:
        assert f in a, f"Handoff 모델에 {f} 필드 누락"


def test_handoff_in_models_init():
    from app.models import Handoff as Exported
    assert Exported is Handoff
