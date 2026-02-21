import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)

# 스케줄 설정: 월요일(0) 오전 9시 (UTC 기준 00시 = KST 09시)
SCHEDULE_WEEKDAY = 0  # Monday
SCHEDULE_HOUR = 0     # UTC 0시 = KST 9시


async def send_webhook(content: str, webhook_url: str) -> None:
    """Discord webhook URL로 메시지 전송"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            webhook_url,
            json={"content": content},
        )
        response.raise_for_status()


STATUS_LABELS: dict[TaskStatus, tuple[str, str]] = {
    TaskStatus.DONE: ("✅", "Done"),
    TaskStatus.DOING: ("🔨", "Doing"),
    TaskStatus.TODO: ("📋", "To Do"),
    TaskStatus.BLOCKED: ("🚫", "Blocked"),
}


def _format_task(task: Task) -> str:
    """태스크 블록 포맷: 메타 + 제목(bold) + 내용"""
    assignee = f"@{task.assignee.name}" if task.assignee else "@미지정"
    due = f", 마감 {task.due_date.strftime('%m/%d')}" if task.due_date else ""
    desc_raw = task.description.strip() if task.description else ""
    body = "\n> " + desc_raw.replace("\n", "\n> ") if desc_raw else ""
    return f"> {assignee}{due}\n> **{task.title}**{body}"


def _format_overdue_task(task: Task) -> str:
    """마감 초과 태스크 포맷"""
    assignee = f"@{task.assignee.name}" if task.assignee else "@미지정"
    status_label = STATUS_LABELS.get(task.status, ("", str(task.status.value)))[1]
    due = task.due_date.strftime("%m/%d") if task.due_date else ""
    return f"> {assignee}, 마감 {due}, 현재 {status_label}\n> **{task.title}**"


async def build_project_summary(project_id: UUID, db: AsyncSession, sender_name: str = "") -> str:
    """프로젝트 주간 리포트 생성"""
    now = datetime.utcnow()
    today = datetime(now.year, now.month, now.day)
    week_ago = now - timedelta(days=7)

    date_from = week_ago.strftime("%m/%d")
    date_to = now.strftime("%m/%d")

    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.tasks).selectinload(Task.assignee),
        )
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        return "_프로젝트를 찾을 수 없습니다._"

    lines: list[str] = []
    sender_tag = f"[**{sender_name}**] " if sender_name else ""
    lines.append(f"📊 {sender_tag}**forps 주간 리포트** ({date_from} ~ {date_to})")
    lines.append("")
    lines.append(f"**[{project.name}]**")

    # 지난 7일 내 업데이트된 태스크를 상태별로 분류
    status_groups: dict[TaskStatus, list[Task]] = {
        TaskStatus.DONE: [],
        TaskStatus.DOING: [],
        TaskStatus.TODO: [],
        TaskStatus.BLOCKED: [],
    }

    overdue: list[Task] = []

    for task in project.tasks:
        if task.updated_at >= week_ago:
            status_groups[task.status].append(task)

        if (
            task.due_date
            and task.due_date < today
            and task.status in (TaskStatus.TODO, TaskStatus.DOING)
        ):
            overdue.append(task)

    has_tasks = any(tasks for tasks in status_groups.values())

    if has_tasks:
        for status in (TaskStatus.DONE, TaskStatus.DOING, TaskStatus.TODO, TaskStatus.BLOCKED):
            tasks = status_groups[status]
            if not tasks:
                continue
            emoji, label = STATUS_LABELS[status]
            lines.append(f"{emoji} {label} ({len(tasks)})")
            for t in tasks:
                lines.append(_format_task(t))
            lines.append("")

    if overdue:
        lines.append("⚠️ **마감 초과 태스크**")
        for task in overdue:
            lines.append(_format_overdue_task(task))
        lines.append("")

    if not has_tasks and not overdue:
        lines.append("_지난 7일간 업데이트된 태스크가 없습니다._")

    return "\n".join(lines)


def _seconds_until_next_schedule() -> float:
    """다음 월요일 오전 9시(KST)까지 남은 초 계산"""
    now = datetime.utcnow()
    days_ahead = SCHEDULE_WEEKDAY - now.weekday()
    if days_ahead < 0 or (days_ahead == 0 and now.hour >= SCHEDULE_HOUR):
        days_ahead += 7

    next_run = now.replace(hour=SCHEDULE_HOUR, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
    return (next_run - now).total_seconds()


async def _send_all_project_summaries() -> None:
    """webhook URL이 설정된 프로젝트에 대해 주간 리포트 전송"""
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        stmt = select(Project).where(Project.discord_webhook_url.isnot(None))
        result = await db.execute(stmt)
        projects = list(result.scalars().all())

        for project in projects:
            try:
                summary = await build_project_summary(project.id, db, sender_name="자동 리포트")
                await send_webhook(summary, project.discord_webhook_url)
            except Exception:
                logger.exception("Failed to send weekly summary for project %s", project.id)


async def start_weekly_scheduler() -> None:
    """매주 월요일 오전 9시(KST)에 주간 리포트 자동 전송"""
    while True:
        wait_seconds = _seconds_until_next_schedule()
        logger.info("Next weekly report in %.0f seconds", wait_seconds)
        await asyncio.sleep(wait_seconds)
        try:
            await _send_all_project_summaries()
        except Exception:
            logger.exception("Weekly scheduler error")
