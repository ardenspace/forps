"""plan_parser_service — PLAN.md 파싱 단위 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §6.1, §10.1
"""

from pathlib import Path

import pytest

from app.services.plan_parser_service import parse_plan


FIXTURE = (Path(__file__).parent / "fixtures" / "plan_sample.md").read_text()


def test_parse_plan_extracts_sprint_name():
    plan = parse_plan(FIXTURE)
    assert plan.sprint_name == "2026-04 로그인 리뉴얼"


def test_parse_plan_extracts_tasks():
    plan = parse_plan(FIXTURE)
    assert len(plan.tasks) == 3
    ids = [t.external_id for t in plan.tasks]
    assert ids == ["task-001", "task-002", "task-003"]


def test_parse_plan_task_fields():
    plan = parse_plan(FIXTURE)
    t1 = plan.tasks[0]
    assert t1.external_id == "task-001"
    assert t1.title == "로그인 UI 리뉴얼"
    assert t1.checked is False
    assert t1.assignee == "alice"
    assert t1.paths == ["frontend/screens/Login.tsx", "frontend/components/auth/"]


def test_parse_plan_checked_status():
    plan = parse_plan(FIXTURE)
    t3 = plan.tasks[2]
    assert t3.external_id == "task-003"
    assert t3.checked is True


def test_parse_plan_ignores_note_section():
    """## 노트 안의 체크박스는 무시 (task-999 가 들어가면 안 됨)."""
    plan = parse_plan(FIXTURE)
    ids = [t.external_id for t in plan.tasks]
    assert "task-999" not in ids
