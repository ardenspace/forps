"""fingerprint_service 단위 테스트.

설계서: 2026-05-01-error-log-phase3-design.md §2.1, §2.2
"""

import hashlib
import pytest

from app.services import fingerprint_service


# ---- 정규화 — 경로 ----

def test_normalize_path_uses_env_var(monkeypatch: pytest.MonkeyPatch):
    """APP_PROJECT_ROOT env var 우선 strip."""
    monkeypatch.setattr(fingerprint_service.settings, "app_project_root", "myapp/")
    result = fingerprint_service._normalize_path("/Users/dev/myapp/routers/x.py")
    assert result == "myapp/routers/x.py"


def test_normalize_path_falls_back_to_heuristic(monkeypatch: pytest.MonkeyPatch):
    """env var 매칭 안 되면 휴리스틱 (`backend/` 첫 segment)."""
    monkeypatch.setattr(fingerprint_service.settings, "app_project_root", "nonexistent/")
    result = fingerprint_service._normalize_path("/Users/dev/app-chak/backend/routers/x.py")
    assert result == "backend/routers/x.py"


def test_normalize_path_keeps_unmatched_original():
    """env var / 휴리스틱 둘 다 안 맞으면 원본 그대로."""
    result = fingerprint_service._normalize_path("/var/log/random.py")
    assert result == "/var/log/random.py"


# ---- fingerprint 결정성 ----

def test_compute_same_func_different_line_same_fingerprint():
    """같은 함수, 다른 line → 같은 fingerprint (line 제거)."""
    frames_a = [{"filename": "/app/backend/x.py", "lineno": 10, "name": "do_thing"}]
    frames_b = [{"filename": "/app/backend/x.py", "lineno": 25, "name": "do_thing"}]
    fp_a = fingerprint_service.compute(
        exception_class="ValueError", stack_frames=frames_a,
    )
    fp_b = fingerprint_service.compute(
        exception_class="ValueError", stack_frames=frames_b,
    )
    assert fp_a == fp_b
    assert len(fp_a) == 40  # SHA1 hex


def test_compute_memory_address_masked():
    """함수명 안의 0x... → 같은 fingerprint."""
    frames_a = [{"filename": "/app/backend/x.py", "lineno": 1, "name": "<lambda at 0x7f8a1234>"}]
    frames_b = [{"filename": "/app/backend/x.py", "lineno": 1, "name": "<lambda at 0xdeadbeef>"}]
    fp_a = fingerprint_service.compute(
        exception_class="ValueError", stack_frames=frames_a,
    )
    fp_b = fingerprint_service.compute(
        exception_class="ValueError", stack_frames=frames_b,
    )
    assert fp_a == fp_b


def test_compute_framework_frames_skipped():
    """site-packages frame 추가해도 같은 fingerprint (앱 frame top 5 만)."""
    app_frame = {"filename": "/app/backend/x.py", "lineno": 1, "name": "do_thing"}
    framework_frame = {
        "filename": "/usr/lib/python3.12/site-packages/uvicorn/server.py",
        "lineno": 50, "name": "serve",
    }
    fp_app_only = fingerprint_service.compute(
        exception_class="ValueError", stack_frames=[app_frame],
    )
    fp_with_framework = fingerprint_service.compute(
        exception_class="ValueError", stack_frames=[framework_frame, app_frame],
    )
    assert fp_app_only == fp_with_framework


def test_compute_class_change_changes_fingerprint():
    """exception class 다름 → 다른 fingerprint."""
    frames = [{"filename": "/app/backend/x.py", "lineno": 1, "name": "do_thing"}]
    fp_value = fingerprint_service.compute(
        exception_class="ValueError", stack_frames=frames,
    )
    fp_key = fingerprint_service.compute(
        exception_class="KeyError", stack_frames=frames,
    )
    assert fp_value != fp_key


# ---- Fallback ----

def test_compute_fallback_when_no_stack_frames():
    """stack_frames None → SHA1(class + "|" + message 첫 줄)."""
    fp = fingerprint_service.compute(
        exception_class="KeyError", stack_frames=None,
        exception_message="'preference'\nstack...",
    )
    expected = hashlib.sha1(b"KeyError|'preference'").hexdigest()
    assert fp == expected


def test_compute_fallback_when_all_framework():
    """모두 framework frame → 가용한 frame top 5 사용 (스킵 무시)."""
    framework_frames = [
        {"filename": "/usr/lib/python3.12/site-packages/asyncio/runners.py",
         "lineno": 50, "name": "run"},
        {"filename": "/usr/lib/python3.12/site-packages/uvicorn/main.py",
         "lineno": 100, "name": "main"},
    ]
    fp = fingerprint_service.compute(
        exception_class="RuntimeError", stack_frames=framework_frames,
    )
    # framework 만 있어도 fingerprint 가 만들어짐 (None fallback 아닌 정규화 경로)
    assert len(fp) == 40
    # 같은 framework frames 면 결정적
    fp2 = fingerprint_service.compute(
        exception_class="RuntimeError", stack_frames=framework_frames,
    )
    assert fp == fp2
