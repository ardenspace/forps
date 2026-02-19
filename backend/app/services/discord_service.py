from datetime import datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.project import Project
from app.models.task import Task, TaskStatus


async def send_webhook(content: str) -> None:
    """Discord webhook URL로 메시지 전송"""
    if not settings.discord_webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL is not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.discord_webhook_url,
            json={"content": content},
        )
        response.raise_for_status()


async def build_weekly_summary(workspace_id: UUID, db: AsyncSession) -> str:
    """지난 7일간 done/blocked 태스크를 프로젝트별로 집계"""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    date_from = week_ago.strftime("%m/%d")
    date_to = now.strftime("%m/%d")

    # 워크스페이스의 모든 프로젝트와 해당 태스크 조회
    stmt = (
        select(Project)
        .where(Project.workspace_id == workspace_id)
        .options(
            selectinload(Project.tasks).selectinload(Task.assignee),
        )
    )
    result = await db.execute(stmt)
    projects = list(result.scalars().all())

    lines: list[str] = []
    lines.append(f"## forps 주간 리포트 ({date_from} ~ {date_to})")
    lines.append("")

    has_content = False

    for project in projects:
        # 지난 7일 내 업데이트된 done/blocked 태스크만 필터
        done_tasks = [
            t for t in project.tasks
            if t.status == TaskStatus.DONE and t.updated_at >= week_ago
        ]
        blocked_tasks = [
            t for t in project.tasks
            if t.status == TaskStatus.BLOCKED and t.updated_at >= week_ago
        ]

        if not done_tasks and not blocked_tasks:
            continue

        has_content = True
        lines.append(f"**[{project.name}]**")

        if done_tasks:
            task_list = ", ".join(
                f"{t.title}(@{t.assignee.name if t.assignee else '미지정'})"
                for t in done_tasks
            )
            lines.append(f"> Done ({len(done_tasks)}): {task_list}")

        if blocked_tasks:
            task_list = ", ".join(
                f"{t.title}(@{t.assignee.name if t.assignee else '미지정'})"
                for t in blocked_tasks
            )
            lines.append(f"> Blocked ({len(blocked_tasks)}): {task_list}")

        lines.append("")

    if not has_content:
        lines.append("_지난 7일간 완료/차단된 태스크가 없습니다._")

    return "\n".join(lines)
