"""GitHub webhook 수신 서비스.

설계서: 2026-04-26-ai-task-automation-design.md §5.1, §7.1
- `verify_signature`: X-Hub-Signature-256 HMAC-SHA256 검증 (constant-time compare)
- `find_project_by_repo_url`: payload.repository.html_url → Project lookup
- `record_push_event`: GitPushEvent INSERT (UNIQUE 충돌 silent skip)
"""

import hashlib
import hmac

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_push_event import GitPushEvent
from app.models.project import Project
from app.schemas.webhook import GitHubPushPayload


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


# GitHub Webhooks API 가 commits 배열을 최대 20개로 잘라서 전달.
# len == 20 이면 truncated 가능성 — Phase 4 sync_service 가 Compare API 로 보정.
GITHUB_WEBHOOK_COMMITS_CAP = 20


async def record_push_event(
    db: AsyncSession,
    project: Project,
    payload: GitHubPushPayload,
) -> GitPushEvent | None:
    """GitPushEvent INSERT. UNIQUE 충돌 시 None 반환 (멱등성).

    Phase 2 범위: raw 보존만. processed_at / error 는 Phase 4 sync_service 가 채움.
    """
    # 롤백 후 ORM 객체 접근 시 expired 오류 방지 — 스칼라 값 미리 캡처.
    project_id = project.id
    head_sha = payload.head_commit.id

    event = GitPushEvent(
        project_id=project_id,
        branch=payload.branch,
        head_commit_sha=head_sha,
        before_commit_sha=payload.before if payload.before and len(payload.before) == 40 else None,
        commits=payload.to_commits_json(),
        commits_truncated=len(payload.commits) >= GITHUB_WEBHOOK_COMMITS_CAP,
        pusher=payload.pusher.name,
    )
    try:
        # SAVEPOINT 사용 — IntegrityError 롤백이 외부 세션 상태를 오염시키지 않도록.
        async with db.begin_nested():
            db.add(event)
    except IntegrityError:
        # UNIQUE (project_id, head_commit_sha) 충돌 → SAVEPOINT 자동 롤백 후 기존 row 반환
        existing = (
            await db.execute(
                select(GitPushEvent).where(
                    GitPushEvent.project_id == project_id,
                    GitPushEvent.head_commit_sha == head_sha,
                )
            )
        ).scalar_one_or_none()
        return existing
    await db.commit()
    await db.refresh(event)
    return event
