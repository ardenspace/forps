from app.models.rate_limit_window import RateLimitWindow


def test_rate_limit_window_fields():
    a = RateLimitWindow.__annotations__
    for f in ["project_id", "token_id", "window_start", "event_count"]:
        assert f in a, f"RateLimitWindow 모델에 {f} 필드 누락"


def test_rate_limit_window_composite_pk():
    """PRIMARY KEY (project_id, token_id, window_start)."""
    pk_cols = {c.name for c in RateLimitWindow.__table__.primary_key.columns}
    assert pk_cols == {"project_id", "token_id", "window_start"}


def test_rate_limit_window_export():
    from app.models import RateLimitWindow as Exported
    assert Exported is RateLimitWindow
