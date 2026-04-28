"""신규/확장 enum 정의 검증 (모델 파일만, alembic 은 Task 11에서)."""
from app.models.task import TaskSource
from app.models.task_event import TaskEventAction


def test_task_source_values():
    assert TaskSource.MANUAL.value == "manual"
    assert TaskSource.SYNCED_FROM_PLAN.value == "synced_from_plan"
    assert {s.value for s in TaskSource} == {"manual", "synced_from_plan"}


def test_task_event_action_existing_preserved():
    """기존 6값이 그대로 살아있어야 한다."""
    assert TaskEventAction.CREATED.value == "created"
    assert TaskEventAction.UPDATED.value == "updated"
    assert TaskEventAction.STATUS_CHANGED.value == "status_changed"
    assert TaskEventAction.ASSIGNED.value == "assigned"
    assert TaskEventAction.COMMENTED.value == "commented"
    assert TaskEventAction.DELETED.value == "deleted"


def test_task_event_action_new_values():
    """Decision Log 2026-04-26 Rev2: 4값 추가."""
    assert TaskEventAction.SYNCED_FROM_PLAN.value == "synced_from_plan"
    assert TaskEventAction.CHECKED_BY_COMMIT.value == "checked_by_commit"
    assert TaskEventAction.UNCHECKED_BY_COMMIT.value == "unchecked_by_commit"
    assert TaskEventAction.ARCHIVED_FROM_PLAN.value == "archived_from_plan"
