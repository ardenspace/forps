"""Task 모델 4 필드 확장 검증 (모델만, alembic 은 Task 11)."""
from datetime import datetime

from app.models.task import Task, TaskSource


def test_task_has_new_fields():
    annotations = Task.__annotations__
    assert "source" in annotations
    assert "external_id" in annotations
    assert "last_commit_sha" in annotations
    assert "archived_at" in annotations


def test_task_source_default_manual():
    """기존 데이터 호환: 새 컬럼 default = MANUAL."""
    t = Task(project_id=None, title="x")  # type: ignore[arg-type]
    assert t.source == TaskSource.MANUAL
    assert t.external_id is None
    assert t.last_commit_sha is None
    assert t.archived_at is None
