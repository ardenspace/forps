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

    sections: list[HandoffSection] = []
    # 날짜 섹션 분리 + 본문 파싱은 후속 task 에서 채움.
    if not any(_DATE_SECTION_RE.match(line) for line in lines):
        raise MalformedHandoffError("no `## YYYY-MM-DD` section found")

    return ParsedHandoff(branch=branch, author_git_login=author, sections=sections)
