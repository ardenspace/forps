"""git-settings endpoints — 프로젝트별 git 연동 설정.

설계서: 2026-04-26-ai-task-automation-design.md §5.2, §9
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.crypto import encrypt_secret
from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.git_settings import GitSettingsResponse, GitSettingsUpdate
from app.services import project_service
from app.services.permission_service import can_manage, get_effective_role

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
