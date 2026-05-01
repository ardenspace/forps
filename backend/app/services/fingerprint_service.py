"""LogEvent 의 결정적 fingerprint 계산.

설계서: 2026-05-01-error-log-phase3-design.md §2.1, §2.2 (spec §4.1, §7)
정규화 6 규칙 — 절대경로→상대 / line 제거 / 메모리 주소 마스킹 / 함수명 유지 / framework 스킵 / SHA1.
"""

import hashlib
import re
from typing import Any

from app.config import settings


_MEMORY_ADDR_RE = re.compile(r"0x[0-9a-f]+")
_FRAMEWORK_PATTERNS = [
    "site-packages/",
    "dist-packages/",
    "asyncio/",
    "uvicorn/",
    "_bootstrap.py",
]
_FRAMEWORK_LIB_RE = re.compile(r"lib/python\d")


def _normalize_path(filename: str) -> str:
    """절대경로 → 상대경로. APP_PROJECT_ROOT env var 우선, 휴리스틱 fallback."""
    project_root = getattr(settings, "app_project_root", "backend/")
    if project_root and project_root in filename:
        idx = filename.find(project_root)
        return filename[idx:]
    for marker in ("backend/", "src/"):
        if marker in filename:
            idx = filename.find(marker)
            return filename[idx:]
    return filename


def _is_framework_frame(filename: str) -> bool:
    """framework / stdlib frame 인지 판정."""
    if any(pattern in filename for pattern in _FRAMEWORK_PATTERNS):
        return True
    if _FRAMEWORK_LIB_RE.search(filename):
        return True
    return False


def _mask_memory_addresses(text: str) -> str:
    """`0x7f8a...` → `0xADDR`."""
    return _MEMORY_ADDR_RE.sub("0xADDR", text)


def compute(
    *,
    exception_class: str,
    stack_frames: list[dict[str, Any]] | None,
    exception_message: str | None = None,
) -> str:
    """결정적 fingerprint SHA1.

    설계서 §2.1 정규화 6 규칙 + §2.2 fallback.
    """
    # Fallback 1 — stack_frames 없음
    if not stack_frames:
        msg_first = (exception_message or "").splitlines()[0] if exception_message else ""
        msg_first = _mask_memory_addresses(msg_first)
        return hashlib.sha1(
            f"{exception_class}|{msg_first}".encode("utf-8")
        ).hexdigest()

    # 앱 frame 만 추출
    app_frames = [
        f for f in stack_frames
        if not _is_framework_frame(f.get("filename", ""))
    ]

    # Fallback 2 — 모두 framework — 가용 frame top 5 (스킵 무시)
    frames_to_use = app_frames if app_frames else stack_frames
    top5 = frames_to_use[:5]

    # 입력 문자열 조립 (line 제거 + 메모리 주소 마스킹)
    parts = []
    for frame in top5:
        rel_path = _normalize_path(frame.get("filename", ""))
        func_name = _mask_memory_addresses(frame.get("name", ""))
        parts.append(f"{rel_path}:{func_name}")

    input_str = f"{exception_class}|" + "\n".join(parts)
    return hashlib.sha1(input_str.encode("utf-8")).hexdigest()
