"""log-ingest 서비스 — 토큰 검증 / rate limit / batch INSERT.

설계서: 2026-05-01-error-log-phase2-ingest-design.md §3.1
"""

import asyncio
import json as _json
import logging
import re
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_event import LogEvent, LogLevel
from app.models.log_ingest_token import LogIngestToken
from app.models.rate_limit_window import RateLimitWindow
from app.schemas.log_ingest import LogEventInput

logger = logging.getLogger(__name__)


def _invalid_token() -> HTTPException:
    """timing attack 회피용 통일 401 — 사유 구분 안 함."""
    return HTTPException(status_code=401, detail="Invalid token")


async def parse_token(authorization_header: str | None) -> tuple[UUID, str]:
    """Bearer <key_id>.<secret> → (key_id_uuid, secret).

    형식 깨짐 → 401. key_id UUID parse fail → 401.
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise _invalid_token()
    raw = authorization_header[len("Bearer "):]
    if "." not in raw:
        raise _invalid_token()
    # key_id 와 secret 분리 — secret 안의 . 도 허용 (key_id 는 UUID 라 . 없음)
    key_id_str, _, secret = raw.partition(".")
    if not secret:
        raise _invalid_token()
    try:
        key_id = UUID(key_id_str)
    except (ValueError, AttributeError):
        raise _invalid_token()
    return key_id, secret


async def verify_token(db: AsyncSession, key_id: UUID, secret: str) -> LogIngestToken:
    """key_id lookup → bcrypt verify → last_used_at 갱신 (in-memory).

    실패 시 401 (사유 구분 안 함). 성공 시 token 반환.
    DB commit 은 caller (ingest_batch) 가 묶음.
    """
    token = await db.get(LogIngestToken, key_id)
    if token is None:
        raise _invalid_token()
    if token.revoked_at is not None:
        raise _invalid_token()

    # bcrypt 동기 — async endpoint 에서 event loop block 회피
    is_valid = await asyncio.to_thread(
        bcrypt.checkpw,
        secret.encode("utf-8"),
        token.secret_hash.encode("utf-8"),
    )
    if not is_valid:
        raise _invalid_token()

    token.last_used_at = datetime.utcnow()
    return token


async def check_rate_limit(
    db: AsyncSession,
    *,
    project_id: UUID,
    token: LogIngestToken,
    batch_size: int,
    now: datetime,
) -> None:
    """RateLimitWindow UPSERT (분 truncate). limit 초과 시 429.

    PostgreSQL ON CONFLICT DO UPDATE pattern — 단일 SQL.
    """
    window_start = now.replace(second=0, microsecond=0)

    stmt = pg_insert(RateLimitWindow).values(
        project_id=project_id,
        token_id=token.id,
        window_start=window_start,
        event_count=batch_size,
    ).on_conflict_do_update(
        index_elements=["project_id", "token_id", "window_start"],
        set_={"event_count": RateLimitWindow.event_count + batch_size},
    ).returning(RateLimitWindow.event_count)

    result = await db.execute(stmt)
    new_count = result.scalar_one()

    if new_count > token.rate_limit_per_minute:
        # 다음 분까지 남은 초 (최대 60)
        next_minute = window_start + timedelta(minutes=1)
        seconds_remaining = max(1, int((next_minute - now).total_seconds()))
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(seconds_remaining)},
        )


_VERSION_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_EXTRA_MAX_BYTES = 4 * 1024  # 4KB


def validate_event(
    event_dict: dict[str, Any], index: int, project_id: UUID,
) -> tuple[LogEvent | None, dict | None]:
    """단일 event dict 검증 — Pydantic + version_sha 형식 + extra 크기.

    valid → (LogEvent, None). invalid → (None, {"index": index, "reason": "..."}).
    """
    # Pydantic schema validate
    try:
        parsed = LogEventInput.model_validate(event_dict)
    except ValidationError as e:
        first = e.errors()[0]
        loc = ".".join(str(x) for x in first["loc"])
        msg = first["msg"]
        return None, {"index": index, "reason": f"{loc}: {msg}"}

    # version_sha 형식
    if parsed.version_sha != "unknown" and not _VERSION_SHA_RE.match(parsed.version_sha):
        return None, {"index": index, "reason": "version_sha format invalid"}

    # extra 크기 (JSON 직렬화 후 byte 수)
    if parsed.extra is not None:
        extra_bytes = len(_json.dumps(parsed.extra).encode("utf-8"))
        if extra_bytes > _EXTRA_MAX_BYTES:
            return None, {"index": index, "reason": f"extra exceeds {_EXTRA_MAX_BYTES} bytes"}

    # LogLevel 정규화 (대소문자 무관)
    try:
        level = LogLevel(parsed.level.lower())
    except ValueError:
        return None, {"index": index, "reason": f"level invalid: {parsed.level}"}

    # timezone-aware → naive UTC (DB 컬럼 TIMESTAMP WITHOUT TIME ZONE)
    emitted_at = parsed.emitted_at
    if emitted_at.tzinfo is not None:
        emitted_at = emitted_at.replace(tzinfo=None)

    log_event = LogEvent(
        project_id=project_id,
        level=level,
        message=parsed.message,
        logger_name=parsed.logger_name,
        version_sha=parsed.version_sha,
        environment=parsed.environment,
        hostname=parsed.hostname,
        emitted_at=emitted_at,
        exception_class=parsed.exception_class,
        exception_message=parsed.exception_message,
        stack_trace=parsed.stack_trace,
        stack_frames=[f.model_dump() for f in parsed.stack_frames] if parsed.stack_frames else None,
        user_id_external=parsed.user_id_external,
        request_id=parsed.request_id,
        extra=parsed.extra,
    )
    return log_event, None


async def insert_events(db: AsyncSession, events: list[LogEvent]) -> int:
    """batch INSERT — fingerprint=NULL (Phase 3 의 fingerprint_service 가 처리).

    단일 트랜잭션. flush 만 (commit 은 caller).
    """
    db.add_all(events)
    await db.flush()
    return len(events)


async def ingest_batch(
    db: AsyncSession,
    *,
    token: LogIngestToken,
    payload_dict: dict[str, Any],
    dropped_since_last: int | None = None,
    now: datetime | None = None,
) -> tuple[int, list[dict]]:
    """end-to-end: rate limit → validate (partial) → insert → commit.

    Returns: (accepted_count, rejected_list).
    payload_dict 의 events 가 없거나 빈 리스트면 caller (endpoint) 가 400 매핑하도록 raise.
    """
    if dropped_since_last is not None and dropped_since_last > 0:
        logger.warning(
            "log_ingest token=%s dropped %d events since last batch",
            token.id, dropped_since_last,
        )

    events_raw = payload_dict.get("events")
    if not isinstance(events_raw, list) or not events_raw:
        # caller 가 400 매핑 — 빈/잘못된 events
        raise HTTPException(status_code=400, detail="events list required and non-empty")

    now = now or datetime.utcnow()

    # last_used_at 갱신 (verify_token 이 in-memory 설정했을 수도 있고, 직접 호출일 수도 있음)
    token.last_used_at = now

    # rate limit — 전체 batch_size 기준
    await check_rate_limit(
        db, project_id=token.project_id, token=token,
        batch_size=len(events_raw), now=now,
    )

    # per-event validate (partial success)
    accepted: list[LogEvent] = []
    rejected: list[dict] = []
    for index, event_dict in enumerate(events_raw):
        log_event, rejection = validate_event(event_dict, index, token.project_id)
        if log_event is not None:
            accepted.append(log_event)
        else:
            rejected.append(rejection)

    if accepted:
        await insert_events(db, accepted)

    # token.last_used_at + RateLimitWindow + LogEvent batch 모두 commit
    await db.commit()

    return len(accepted), rejected
