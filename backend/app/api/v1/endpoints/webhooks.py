from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.workspace import WorkspaceRole
from app.services import workspace_service
from app.services.discord_service import build_weekly_summary, send_webhook

router = APIRouter(prefix="/workspaces", tags=["webhooks"])


@router.post("/{workspace_id}/discord-summary")
async def send_discord_summary(
    workspace_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Discord로 주간 요약 리포트 전송 (Owner만)"""
    workspace = await workspace_service.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    membership = await workspace_service.get_user_membership(db, workspace_id, user.id)
    if not membership or membership.role != WorkspaceRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can send Discord summary")

    from app.config import settings

    if not settings.discord_webhook_url:
        raise HTTPException(status_code=400, detail="Discord webhook URL is not configured")

    summary = await build_weekly_summary(workspace_id, db)
    await send_webhook(summary)

    return {"message": "Discord summary sent successfully"}
