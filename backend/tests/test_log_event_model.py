from app.models.log_event import LogEvent, LogLevel


def test_log_level_enum():
    """설계서 §4.1 — 5 레벨."""
    assert {l.value for l in LogLevel} == {"debug", "info", "warning", "error", "critical"}


def test_log_event_fields():
    a = LogEvent.__annotations__
    for f in [
        "id", "project_id", "level", "message", "logger_name",
        "version_sha", "environment", "hostname",
        "emitted_at", "received_at",
        "exception_class", "exception_message", "stack_trace", "stack_frames",
        "fingerprint", "fingerprinted_at",
        "user_id_external", "request_id", "extra",
    ]:
        assert f in a, f"LogEvent 모델에 {f} 필드 누락"


def test_log_event_export():
    from app.models import LogEvent as Exported, LogLevel as ExportedLevel
    assert Exported is LogEvent
    assert ExportedLevel is LogLevel
