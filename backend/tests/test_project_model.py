"""Project 모델 git 6 필드 확장 검증 (모델만, alembic 은 Task 11)."""
from sqlalchemy.orm import Mapped

from app.models.project import Project


def test_project_has_git_fields():
    """6 필드가 모델에 정의되어 있어야 한다."""
    annotations = Project.__annotations__
    assert "git_repo_url" in annotations
    assert "git_default_branch" in annotations
    assert "plan_path" in annotations
    assert "handoff_dir" in annotations
    assert "last_synced_commit_sha" in annotations
    assert "webhook_secret_encrypted" in annotations


def test_project_git_default_branch_default():
    """git_default_branch 의 default 값이 'main'."""
    p = Project(workspace_id=None, name="t")  # type: ignore[arg-type]
    assert p.git_default_branch == "main"
    assert p.plan_path == "PLAN.md"
    assert p.handoff_dir == "handoffs/"
