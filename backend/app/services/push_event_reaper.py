"""부팅 시 미처리 GitPushEvent 회수.

설계서: 2026-04-26-ai-task-automation-design.md §5.1 (⑧), §7.1
컨테이너 재시작/크래시로 BackgroundTask 가 실행되지 못한 이벤트 보존.

쿼리: processed_at IS NULL AND received_at < now() - 5min
   → 5분은 정상 처리 grace period (현재 처리 중인 BackgroundTask 와 충돌 회피)

Phase 2 범위: 쿼리 + callback 호출만. callback이 None 이면 logging only.
Phase 4 에서 sync_service.process_event 가 callback 으로 주입됨.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.git_push_event import GitPushEvent

logger = logging.getLogger(__name__)


REAPER_GRACE = timedelta(minutes=5)


ProcessCallback = Callable[[GitPushEvent], Awaitable[None]]


async def reap_pending_events(
    db: AsyncSession,
    callback: ProcessCallback | None,
) -> int:
    """미처리 이벤트 조회 → callback 호출. 처리된 이벤트 수 반환.

    callback이 None 이면 로깅만 — Phase 2 placeholder.
    callback 안에서 예외 raise 시 다음 이벤트로 진행 (개별 격리).
    """
    cutoff = datetime.utcnow() - REAPER_GRACE
    stmt = (
        select(GitPushEvent)
        .where(GitPushEvent.processed_at.is_(None))
        .where(GitPushEvent.received_at < cutoff)
        .order_by(GitPushEvent.received_at)
    )
    rows = (await db.execute(stmt)).scalars().all()

    for event in rows:
        if callback is None:
            logger.info(
                "pending push event %s (project=%s, branch=%s, sha=%s) — Phase 2 stub",
                event.id,
                event.project_id,
                event.branch,
                event.head_commit_sha,
            )
            continue
        try:
            await callback(event)
        except Exception:
            logger.exception(
                "reaper callback failed for event %s — leaving processed_at NULL",
                event.id,
            )

    return len(rows)


async def run_reaper_once() -> int:
    """app startup 에서 호출 — 자체 세션 열고 reaper 1회 실행."""
    async with AsyncSessionLocal() as session:
        return await reap_pending_events(session, callback=None)
