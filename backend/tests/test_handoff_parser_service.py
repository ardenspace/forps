"""handoff_parser_service — handoff-{branch}.md 파싱 단위 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §6.2, §10.1
"""

from pathlib import Path

import pytest

from app.services.handoff_parser_service import (
    MalformedHandoffError,
    parse_handoff,
)


FIXTURE = (Path(__file__).parent / "fixtures" / "handoff_sample.md").read_text()


def test_parse_handoff_extracts_branch_and_author():
    h = parse_handoff(FIXTURE)
    assert h.branch == "feature/login-redesign"
    assert h.author_git_login == "alice"


def test_parse_handoff_missing_header_raises():
    text = "## 2026-04-26\n- [x] task-001\n"
    with pytest.raises(MalformedHandoffError):
        parse_handoff(text)


def test_parse_handoff_empty_text_raises():
    with pytest.raises(MalformedHandoffError):
        parse_handoff("")


def test_parse_handoff_branch_with_slash_preserved():
    text = "# Handoff: release/v1.2.3 — @bob\n\n## 2026-04-29\n- [ ] task-001\n"
    h = parse_handoff(text)
    assert h.branch == "release/v1.2.3"
    assert h.author_git_login == "bob"


def test_parse_handoff_two_date_sections():
    h = parse_handoff(FIXTURE)
    assert len(h.sections) == 2
    assert h.sections[0].date == "2026-04-26"
    assert h.sections[1].date == "2026-04-25"


def test_parse_handoff_sections_sorted_desc_regardless_of_input_order():
    """입력에서 옛날 날짜가 먼저 나와도 정렬 결과는 desc."""
    text = """# Handoff: feature/x — @alice

## 2026-04-25

- [ ] task-1

## 2026-04-29

- [x] task-2
"""
    h = parse_handoff(text)
    assert [s.date for s in h.sections] == ["2026-04-29", "2026-04-25"]


def test_parse_handoff_single_section():
    text = """# Handoff: main — @bob

## 2026-04-29

- [ ] task-001
"""
    h = parse_handoff(text)
    assert len(h.sections) == 1
    assert h.sections[0].date == "2026-04-29"
