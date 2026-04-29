"""GitHub webhook 수신 서비스.

설계서: 2026-04-26-ai-task-automation-design.md §5.1, §7.1
- `verify_signature`: X-Hub-Signature-256 HMAC-SHA256 검증 (constant-time compare)
- `find_project_by_repo_url`: payload.repository.html_url → Project lookup
- `record_push_event`: GitPushEvent INSERT (UNIQUE 충돌 silent skip)
"""

import hashlib
import hmac


def verify_signature(body: bytes, signature: str | None, secret: str) -> bool:
    """`X-Hub-Signature-256` HMAC-SHA256 검증. constant-time compare.

    GitHub 형식: `sha256=<hex>`. prefix 없거나 None이면 fail.
    """
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    received = signature[len("sha256="):]
    return hmac.compare_digest(expected, received)
