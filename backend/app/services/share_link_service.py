import secrets
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.share_link import ShareLink, ShareLinkScope
from app.models.task import Task


async def create_share_link(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    scope: ShareLinkScope = ShareLinkScope.PROJECT_READ,
) -> ShareLink:
    """프로젝트에 대한 공유 링크 생성 (30일 만료)"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=30)

    share_link = ShareLink(
        project_id=project_id,
        created_by=user_id,
        token=token,
        scope=scope,
        expires_at=expires_at,
    )
    db.add(share_link)
    await db.commit()
    await db.refresh(share_link)
    return share_link


async def get_share_link_by_token(db: AsyncSession, token: str) -> ShareLink | None:
    """토큰으로 공유 링크 조회"""
    stmt = select(ShareLink).where(
        ShareLink.token == token,
        ShareLink.is_active == True,
    )
    result = await db.execute(stmt)
    share_link = result.scalar_one_or_none()

    if share_link and share_link.expires_at < datetime.utcnow():
        # 만료된 경우
        return None

    return share_link


async def get_project_share_links(db: AsyncSession, project_id: UUID) -> list[ShareLink]:
    """프로젝트의 공유 링크 목록"""
    stmt = (
        select(ShareLink)
        .where(ShareLink.project_id == project_id)
        .order_by(ShareLink.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def deactivate_share_link(db: AsyncSession, share_link_id: UUID) -> bool:
    """공유 링크 비활성화"""
    stmt = select(ShareLink).where(ShareLink.id == share_link_id)
    result = await db.execute(stmt)
    share_link = result.scalar_one_or_none()

    if not share_link:
        return False

    share_link.is_active = False
    await db.commit()
    return True


async def get_shared_project_data(db: AsyncSession, share_link: ShareLink) -> dict:
    """공유 링크를 통해 접근 가능한 프로젝트 데이터 반환"""
    # 프로젝트 조회
    stmt = select(Project).where(Project.id == share_link.project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        return {"project_name": "Unknown", "tasks": []}

    # 태스크 목록 조회
    stmt = (
        select(Task)
        .where(Task.project_id == share_link.project_id)
        .options(selectinload(Task.assignee))
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return {
        "project_name": project.name,
        "tasks": [
            {
                "id": str(task.id),
                "title": task.title,
                "status": task.status.value,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "assignee_name": task.assignee.name if task.assignee else None,
            }
            for task in tasks
        ],
    }
