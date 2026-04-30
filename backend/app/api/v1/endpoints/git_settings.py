"""git-settings endpoints — 프로젝트별 git 연동 설정.

설계서: 2026-04-26-ai-task-automation-design.md §5.2, §9
"""

import logging
from uuid import UUID

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.crypto import decrypt_secret, encrypt_secret, generate_webhook_secret
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.git_push_event import GitPushEvent
from app.models.handoff import Handoff
from app.schemas.git_settings import (
    GitSettingsResponse,
    GitSettingsUpdate,
    HandoffSummary,
    ReprocessResponse,
    WebhookRegisterResponse,
)
from app.services import github_hook_service, project_service
from app.services.permission_service import can_manage, get_effective_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["git-settings"])


def _public_webhook_url() -> str:
    base = settings.forps_public_url.rstrip("/")
    return f"{base}/api/v1/webhooks/github"


@router.get("/{project_id}/git-settings", response_model=GitSettingsResponse)
async def get_git_settings(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return GitSettingsResponse(
        git_repo_url=project.git_repo_url,
        git_default_branch=project.git_default_branch,
        plan_path=project.plan_path,
        handoff_dir=project.handoff_dir,
        last_synced_commit_sha=project.last_synced_commit_sha,
        has_webhook_secret=project.webhook_secret_encrypted is not None,
        has_github_pat=project.github_pat_encrypted is not None,
        public_webhook_url=_public_webhook_url(),
    )


@router.patch("/{project_id}/git-settings", response_model=GitSettingsResponse)
async def patch_git_settings(
    project_id: UUID,
    update: GitSettingsUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Owner only")

    data = update.model_dump(exclude_unset=True)
    for key in ("git_repo_url", "git_default_branch", "plan_path", "handoff_dir"):
        if key in data:
            setattr(project, key, data[key])
    if "github_pat" in data and data["github_pat"]:
        project.github_pat_encrypted = encrypt_secret(data["github_pat"])

    await db.commit()
    await db.refresh(project)

    return GitSettingsResponse(
        git_repo_url=project.git_repo_url,
        git_default_branch=project.git_default_branch,
        plan_path=project.plan_path,
        handoff_dir=project.handoff_dir,
        last_synced_commit_sha=project.last_synced_commit_sha,
        has_webhook_secret=project.webhook_secret_encrypted is not None,
        has_github_pat=project.github_pat_encrypted is not None,
        public_webhook_url=_public_webhook_url(),
    )


@router.post(
    "/{project_id}/git-settings/webhook",
    response_model=WebhookRegisterResponse,
)
async def register_webhook(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """GitHub repo 에 push webhook 자동 등록 (또는 갱신).

    - 같은 callback url 의 hook 이 있으면 PATCH (config.secret 갱신)
    - 없으면 POST (신규 등록)
    - 새 webhook_secret 항상 생성 — 기존 secret 무효화 (regenerate 의 부수 효과)
    """
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Owner only")

    if not project.git_repo_url:
        raise HTTPException(status_code=400, detail="git_repo_url 미설정")
    if project.github_pat_encrypted is None:
        raise HTTPException(status_code=400, detail="GitHub PAT 미설정")

    try:
        pat = decrypt_secret(project.github_pat_encrypted)
    except InvalidToken:
        logger.error("PAT 복호화 실패 — Fernet 마스터 키 mismatch project=%s", project_id)
        raise HTTPException(status_code=500, detail="PAT 복호화 실패")

    callback_url = _public_webhook_url()
    new_secret = generate_webhook_secret()

    existing_hooks = await github_hook_service.list_hooks(project.git_repo_url, pat)
    matching = next(
        (h for h in existing_hooks if h.get("config", {}).get("url") == callback_url),
        None,
    )

    if matching is not None:
        hook = await github_hook_service.update_hook(
            project.git_repo_url, pat,
            hook_id=matching["id"],
            callback_url=callback_url,
            secret=new_secret,
        )
        was_existing = True
    else:
        hook = await github_hook_service.create_hook(
            project.git_repo_url, pat,
            callback_url=callback_url,
            secret=new_secret,
        )
        was_existing = False

    project.webhook_secret_encrypted = encrypt_secret(new_secret)
    await db.commit()

    return WebhookRegisterResponse(
        webhook_id=hook["id"],
        was_existing=was_existing,
        public_webhook_url=callback_url,
    )


@router.get("/{project_id}/handoffs", response_model=list[HandoffSummary])
async def list_handoffs(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    branch: str | None = None,
    limit: int = 50,
):
    """프로젝트의 handoff 이력 조회 (branch 필터 + limit clamp)."""
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = await get_effective_role(db, user.id, project_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")

    limit = max(1, min(limit, 200))

    stmt = (
        select(Handoff)
        .where(Handoff.project_id == project_id)
        .order_by(Handoff.pushed_at.desc())
        .limit(limit)
    )
    if branch is not None:
        stmt = stmt.where(Handoff.branch == branch)

    rows = (await db.execute(stmt)).scalars().all()
    return [
        HandoffSummary(
            id=h.id,
            branch=h.branch,
            author_git_login=h.author_git_login,
            commit_sha=h.commit_sha,
            pushed_at=h.pushed_at,
            parsed_tasks_count=len(h.parsed_tasks or []),
        )
        for h in rows
    ]


@router.post(
    "/{project_id}/git-events/{event_id}/reprocess",
    response_model=ReprocessResponse,
)
async def reprocess_git_event(
    project_id: UUID,
    event_id: UUID,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """실패한 git push event 를 수동으로 재처리 큐에 추가 (OWNER 전용)."""
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = await get_effective_role(db, user.id, project_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Owner only")

    event = await db.get(GitPushEvent, event_id)
    if event is None or event.project_id != project_id:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.processed_at is not None and event.error is None:
        raise HTTPException(
            status_code=400,
            detail="Event already processed successfully — nothing to reprocess",
        )

    event.processed_at = None
    event.error = None
    await db.commit()

    # BackgroundTask — Phase 4 webhook endpoint 의 _run_sync_in_new_session 재사용.
    # module-level 참조를 통해 호출해야 테스트 monkeypatch 가 동작함.
    from app.api.v1.endpoints import webhooks as webhooks_module
    background_tasks.add_task(webhooks_module._run_sync_in_new_session, event_id)

    return ReprocessResponse(event_id=event_id, status="queued")
