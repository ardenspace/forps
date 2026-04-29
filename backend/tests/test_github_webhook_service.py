"""github_webhook_service — 서명 검증 / repo 매칭 / GitPushEvent INSERT 단위 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §10.2
"""

import hashlib
import hmac
import json
from pathlib import Path

import pytest

from app.services.github_webhook_service import verify_signature


FIXTURE = (Path(__file__).parent / "fixtures" / "github_push_payload.json").read_bytes()


def _sign(body: bytes, secret: str) -> str:
    """`X-Hub-Signature-256` 형식과 동일하게 HMAC-SHA256 생성."""
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def test_verify_signature_pass():
    secret = "the-shared-webhook-secret"
    sig = _sign(FIXTURE, secret)
    assert verify_signature(FIXTURE, sig, secret) is True


def test_verify_signature_fail_wrong_secret():
    sig = _sign(FIXTURE, "the-real-secret")
    assert verify_signature(FIXTURE, sig, "different-secret") is False


def test_verify_signature_fail_tampered_body():
    secret = "the-shared-webhook-secret"
    sig = _sign(FIXTURE, secret)
    tampered = FIXTURE + b"x"
    assert verify_signature(tampered, sig, secret) is False


def test_verify_signature_missing_prefix():
    """`sha256=` prefix 없으면 reject."""
    secret = "the-shared-webhook-secret"
    mac = hmac.new(secret.encode(), FIXTURE, hashlib.sha256).hexdigest()
    assert verify_signature(FIXTURE, mac, secret) is False  # prefix 빠짐


def test_verify_signature_empty_signature():
    assert verify_signature(FIXTURE, "", "secret") is False
    assert verify_signature(FIXTURE, None, "secret") is False  # type: ignore[arg-type]
