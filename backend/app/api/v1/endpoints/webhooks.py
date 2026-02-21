from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.workspace import WorkspaceRole
from app.services import project_service
from app.services.discord_service import build_project_summary, send_webhook
from app.services.permission_service import get_effective_role

router = APIRouter(prefix="/projects", tags=["webhooks"])


@router.post("/{project_id}/discord-summary")
async def send_discord_summary(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Discord로 주간 요약 리포트 전송 (Owner만)"""
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if role != WorkspaceRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can send Discord summary")

    if not project.discord_webhook_url:
        raise HTTPException(status_code=400, detail="Discord webhook URL이 설정되지 않았습니다. 사이드바에서 설정해주세요.")

    summary = await build_project_summary(project_id, db, sender_name=user.name)
    await send_webhook(summary, project.discord_webhook_url)

    return {"message": "Discord summary sent successfully"}
