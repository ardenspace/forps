from app.models.log_ingest_token import LogIngestToken


def test_log_ingest_token_fields():
    a = LogIngestToken.__annotations__
    for f in [
        "id", "project_id", "name", "secret_hash",
        "created_at", "last_used_at", "revoked_at", "rate_limit_per_minute",
    ]:
        assert f in a, f"LogIngestToken 모델에 {f} 필드 누락"


def test_log_ingest_token_default_rate_limit():
    t = LogIngestToken(project_id=None, name="t", secret_hash="h")  # type: ignore[arg-type]
    assert t.rate_limit_per_minute == 600


def test_log_ingest_token_export():
    from app.models import LogIngestToken as Exported
    assert Exported is LogIngestToken
