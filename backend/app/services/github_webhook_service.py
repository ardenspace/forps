"""GitHub webhook 수신 서비스.

설계서: 2026-04-26-ai-task-automation-design.md §5.1, §7.1
- `verify_signature`: X-Hub-Signature-256 HMAC-SHA256 검증 (constant-time compare)
- `find_project_by_repo_url`: payload.repository.html_url → Project lookup
- `record_push_event`: GitPushEvent INSERT (UNIQUE 충돌 silent skip)
"""

import hashlib
import hmac

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


def verify_signature(body: bytes, signature: str | None, secret: str) -> bool:
    """`X-Hub-Signature-256` HMAC-SHA256 검증. constant-time compare.

    GitHub 형식: `sha256=<hex>`. prefix 없거나 None이면 fail.
    """
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    received = signature[len("sha256="):]
    return hmac.compare_digest(expected, received)


def _normalize_repo_url(url: str) -> str:
    """`.git` suffix / trailing `/` / case 정규화 — html_url vs clone_url 흡수."""
    u = url.strip().lower()
    if u.endswith(".git"):
        u = u[:-4]
    if u.endswith("/"):
        u = u[:-1]
    return u


async def find_project_by_repo_url(
    db: AsyncSession, repo_url: str
) -> Project | None:
    """payload.repository.html_url 또는 clone_url → Project lookup.

    매칭 실패 시 None — 호출자(endpoint)는 200 + 경고 로그로 처리.
    """
    target = _normalize_repo_url(repo_url)
    # 정규화 후 비교: Python 측 정규화로 처리 — 후보 수 적음 가정.
    stmt = select(Project).where(Project.git_repo_url.is_not(None))
    rows = (await db.execute(stmt)).scalars().all()
    for proj in rows:
        if proj.git_repo_url and _normalize_repo_url(proj.git_repo_url) == target:
            return proj
    return None
