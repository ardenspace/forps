"""GitHub push webhook 수신 endpoint.

설계서: 2026-04-26-ai-task-automation-design.md §5.2, §7.1, §8
응답 정책:
  - 401: 서명 검증 실패 (또는 secret 없음 / signature 헤더 없음)
  - 200 + 경고 로그: 알 수 없는 repo (GitHub 재전송 방지)
  - 200: 정상 + GitPushEvent INSERT (중복 commit_sha 도 200, 멱등성)
  - 500: DB 쓰기 실패 (GitHub 자동 재시도)
"""

import logging

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_secret
from app.database import get_db
from app.schemas.webhook import GitHubPushPayload
from app.services.github_webhook_service import (
    find_project_by_repo_url,
    record_push_event,
    verify_signature,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def receive_github_push(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
):
    """GitHub push webhook 수신.

    흐름: body 읽기 → payload 파싱 → repo 매칭 → secret decrypt → 서명 검증 → INSERT.
    Phase 2 범위: raw 보존만. 파싱/sync는 Phase 4.
    """
    body = await request.body()

    # push 이벤트만 처리 — 다른 이벤트는 200 ACK + skip
    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}

    try:
        payload = GitHubPushPayload.model_validate_json(body)
    except ValueError:
        # 깨진 payload — 400 (재전송 의미 없음)
        raise HTTPException(status_code=400, detail="Invalid push payload")

    project = await find_project_by_repo_url(db, payload.repository.html_url)
    if project is None:
        # 알 수 없는 repo: 200 + 경고 로그 (재전송 방지)
        logger.warning(
            "github webhook for unknown repo: %s", payload.repository.html_url
        )
        return {"status": "unknown_repo"}

    if project.webhook_secret_encrypted is None:
        # repo는 등록됐지만 secret 미설정 — 검증 불가, 401
        logger.warning("project %s has git_repo_url but no webhook secret", project.id)
        raise HTTPException(status_code=401, detail="Webhook secret not configured")

    try:
        secret = decrypt_secret(project.webhook_secret_encrypted)
    except InvalidToken:
        logger.error(
            "failed to decrypt webhook secret for project %s — Fernet master key mismatch",
            project.id,
        )
        raise HTTPException(status_code=500, detail="Secret decryption failed")

    if not verify_signature(body, x_hub_signature_256, secret):
        logger.warning(
            "github webhook signature verification failed for project %s", project.id
        )
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = await record_push_event(db, project, payload)
    return {"status": "received", "event_id": str(event.id) if event else None}
