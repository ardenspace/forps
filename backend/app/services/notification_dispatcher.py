"""Discord 알림 dispatcher — disable 정책 통합 진입점.

설계서: 2026-05-01-phase-6-discord-notifications-design.md §3.1
"""
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services import discord_service

logger = logging.getLogger(__name__)

DISABLE_THRESHOLD = 3


async def dispatch_discord_alert(
    db: AsyncSession,
    project: Project,
    content: str,
) -> None:
    """Discord 알림 1점 진입. URL NULL / disabled 체크 + 실패 시 counter 갱신.

    실패가 메인 처리에 영향 안 가도록 catch — caller 는 await 만 하면 됨.
    counter 갱신은 같은 session 의 commit 으로 영속.
    """
    if project.discord_webhook_url is None:
        return
    if project.discord_disabled_at is not None:
        logger.info(
            "Discord disabled for project %s since %s — skip",
            project.id, project.discord_disabled_at,
        )
        return

    try:
        await discord_service.send_webhook(content, project.discord_webhook_url)
        # 성공 — counter > 0 이면 reset
        if project.discord_consecutive_failures > 0:
            project.discord_consecutive_failures = 0
            try:
                await db.commit()
            except Exception:
                logger.exception(
                    "Failed to reset Discord failure counter for project %s",
                    project.id,
                )
    except Exception:
        logger.exception("Discord alert failed for project %s", project.id)
        project.discord_consecutive_failures += 1
        if project.discord_consecutive_failures >= DISABLE_THRESHOLD:
            project.discord_disabled_at = datetime.utcnow()
            logger.warning(
                "Discord auto-disabled for project %s after %d consecutive failures",
                project.id, project.discord_consecutive_failures,
            )
        try:
            await db.commit()
        except Exception:
            logger.exception(
                "Failed to record Discord failure counter for project %s",
                project.id,
            )
