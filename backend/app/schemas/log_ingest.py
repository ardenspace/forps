"""log-ingest 의 wire format Pydantic schemas.

설계서: 2026-05-01-error-log-phase2-ingest-design.md §3.5
DB 컬럼명 = wire 키 이름 (LogEvent 모델 1:1).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StackFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str
    lineno: int
    name: str


class LogEventInput(BaseModel):
    """단일 log event — handler 가 보내는 wire format."""
    model_config = ConfigDict(extra="forbid")

    level: str  # DEBUG/INFO/WARNING/ERROR/CRITICAL — service 가 LogLevel enum 변환
    message: str
    logger_name: str
    version_sha: str
    environment: str
    hostname: str
    emitted_at: datetime

    # 에러 전용 (선택)
    exception_class: str | None = None
    exception_message: str | None = None
    stack_trace: str | None = None
    stack_frames: list[StackFrame] | None = None

    # 컨텍스트 (선택)
    user_id_external: str | None = None
    request_id: str | None = None
    extra: dict[str, Any] | None = None


class IngestPayload(BaseModel):
    """배치 페이로드. events 는 raw dict — service 가 per-event validate (partial success)."""
    model_config = ConfigDict(extra="forbid")
    events: list[dict[str, Any]] = Field(min_length=1)


class RejectedEvent(BaseModel):
    index: int
    reason: str


class IngestResponse(BaseModel):
    accepted: int
    rejected: list[RejectedEvent]
