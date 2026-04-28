from app.models.error_group import ErrorGroup, ErrorGroupStatus


def test_error_group_status_enum():
    """설계서 §4.1 — 4 상태."""
    assert {s.value for s in ErrorGroupStatus} == {"open", "resolved", "ignored", "regressed"}


def test_error_group_fields():
    a = ErrorGroup.__annotations__
    for f in [
        "id", "project_id", "fingerprint", "exception_class",
        "exception_message_sample", "first_seen_at", "first_seen_version_sha",
        "last_seen_at", "last_seen_version_sha", "event_count", "status",
        "resolved_at", "resolved_by_user_id", "resolved_in_version_sha",
        "last_alerted_new_at", "last_alerted_spike_at", "last_alerted_regression_at",
    ]:
        assert f in a, f"ErrorGroup 모델에 {f} 필드 누락"


def test_error_group_default_status_open():
    g = ErrorGroup(
        project_id=None, fingerprint="x", exception_class="X",  # type: ignore[arg-type]
        first_seen_version_sha="a"*40, last_seen_version_sha="a"*40,
    )
    assert g.status == ErrorGroupStatus.OPEN
    assert g.event_count == 0


def test_error_group_export():
    from app.models import ErrorGroup as Exported
    assert Exported is ErrorGroup
