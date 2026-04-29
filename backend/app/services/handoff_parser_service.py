"""handoff-{branch}.md 파서 — 헤더 / 날짜 섹션 / 체크박스 / 자유 영역 추출.

설계서: 2026-04-26-ai-task-automation-design.md §6.2

파싱 단계:
  1) `# Handoff: <branch> — @<user>` 헤더 1개 (없으면 MalformedHandoffError)
  2) `## YYYY-MM-DD` 일자 섹션 ≥1 개 (없으면 MalformedHandoffError)
  3) 각 섹션 안:
     - 들여쓰기 0 인 `- [x]/[ ] task-XXX` → CheckItem
     - 들여쓰기 ≥ 2 인 체크박스 → Subtask (parent = 직전 최상위 체크박스)
     - `### 마지막 커밋` / `### 다음` / `### 블로커` 자유 텍스트 → FreeNotes
  4) sections 정렬: date desc (최신 = sections[0])
"""

import re

from app.schemas.parsed_handoff import (
    CheckItem,
    FreeNotes,
    HandoffSection,
    ParsedHandoff,
    Subtask,
)


class MalformedHandoffError(ValueError):
    """필수 헤더(파일 헤더 또는 일자 섹션) 부재."""


_HEADER_RE = re.compile(
    r"^#\s+Handoff\s*:\s*(?P<branch>\S+)\s+—\s+@(?P<user>[A-Za-z0-9_-]+)\s*$"
)
_DATE_SECTION_RE = re.compile(r"^##\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$")
_FREE_NOTE_HEADERS = {
    "마지막 커밋": "last_commit",
    "다음": "next",
    "블로커": "blockers",
}
_FREE_NOTE_HEADER_RE = re.compile(r"^###\s+(?P<name>.+?)\s*$")
_TOP_CHECK_RE = re.compile(
    r"^-\s+\[(?P<check>[ xX])\]\s+(?P<id>task-[A-Za-z0-9_-]+)\s*(?P<extra>.*?)\s*$"
)
_SUB_CHECK_RE = re.compile(
    r"^(?P<indent>(?:    |\t|  )+)-\s+\[(?P<check>[ xX])\]\s+(?P<text>.+?)\s*$"
)


def parse_handoff(text: str) -> ParsedHandoff:
    """handoff 텍스트 → ParsedHandoff. sections 는 date desc."""
    lines = text.splitlines()
    branch: str | None = None
    author: str | None = None

    for line in lines:
        m = _HEADER_RE.match(line)
        if m:
            branch = m.group("branch")
            author = m.group("user")
            break

    if branch is None or author is None:
        raise MalformedHandoffError("missing or malformed `# Handoff: <branch> — @<user>` header")

    # 날짜 섹션으로 분할
    section_blocks: list[tuple[str, list[str]]] = []  # (date, body_lines)
    current_date: str | None = None
    current_body: list[str] = []
    for line in lines:
        date_match = _DATE_SECTION_RE.match(line)
        if date_match:
            if current_date is not None:
                section_blocks.append((current_date, current_body))
            current_date = date_match.group("date")
            current_body = []
        elif current_date is not None:
            current_body.append(line)
    if current_date is not None:
        section_blocks.append((current_date, current_body))

    if not section_blocks:
        raise MalformedHandoffError("no `## YYYY-MM-DD` section found")

    sections = [
        HandoffSection(date=date, checks=[], subtasks=[], free_notes=FreeNotes())
        for date, _body in section_blocks
    ]
    sections.sort(key=lambda s: s.date, reverse=True)

    return ParsedHandoff(branch=branch, author_git_login=author, sections=sections)
