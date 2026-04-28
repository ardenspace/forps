from app.models.git_push_event import GitPushEvent


def test_git_push_event_fields():
    a = GitPushEvent.__annotations__
    for f in [
        "id", "project_id", "branch", "head_commit_sha", "commits",
        "commits_truncated", "pusher", "received_at", "processed_at", "error",
    ]:
        assert f in a, f"GitPushEvent 모델에 {f} 필드 누락"


def test_git_push_event_export():
    from app.models import GitPushEvent as Exported
    assert Exported is GitPushEvent
