"""ErrorGroup user-driven status transition unit tests.

설계서: 2026-04-26-error-log-design.md §4.1 전이 다이어그램.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace
from app.services import error_group_service


async def _seed_group_user(
    db: AsyncSession, *, status: ErrorGroupStatus = ErrorGroupStatus.OPEN,
) -> tuple[ErrorGroup, User]:
    user = User(
        email=f"u-{uuid4().hex[:8]}@x", name="u", password_hash="x",
    )
    db.add(user)
    await db.flush()
    ws = Workspace(name="w", slug=f"w-{uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.flush()
    now = datetime.utcnow()
    group = ErrorGroup(
        project_id=proj.id, fingerprint="fp",
        exception_class="ValueError", exception_message_sample="x",
        first_seen_at=now, first_seen_version_sha="a" * 40,
        last_seen_at=now, last_seen_version_sha="a" * 40,
        event_count=1, status=status,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    await db.refresh(user)
    return group, user


@pytest.mark.parametrize(
    "from_status,action,to_status",
    [
        (ErrorGroupStatus.OPEN, "resolve", ErrorGroupStatus.RESOLVED),
        (ErrorGroupStatus.OPEN, "ignore", ErrorGroupStatus.IGNORED),
        (ErrorGroupStatus.RESOLVED, "reopen", ErrorGroupStatus.OPEN),
        (ErrorGroupStatus.IGNORED, "unmute", ErrorGroupStatus.OPEN),
        (ErrorGroupStatus.REGRESSED, "resolve", ErrorGroupStatus.RESOLVED),
        (ErrorGroupStatus.REGRESSED, "reopen", ErrorGroupStatus.OPEN),
    ],
)
async def test_legal_transitions(
    async_session: AsyncSession,
    from_status: ErrorGroupStatus,
    action: str,
    to_status: ErrorGroupStatus,
):
    group, user = await _seed_group_user(async_session, status=from_status)
    updated = await error_group_service.transition_status(
        async_session, group, action=action, user_id=user.id,
        resolved_in_version_sha=None,
    )
    assert updated.status == to_status


@pytest.mark.parametrize(
    "from_status,action",
    [
        (ErrorGroupStatus.RESOLVED, "ignore"),
        (ErrorGroupStatus.IGNORED, "resolve"),
        (ErrorGroupStatus.OPEN, "reopen"),     # 이미 OPEN
        (ErrorGroupStatus.RESOLVED, "resolve"),  # 이미 RESOLVED
        (ErrorGroupStatus.IGNORED, "ignore"),  # 이미 IGNORED
    ],
)
async def test_illegal_transitions_raise(
    async_session: AsyncSession,
    from_status: ErrorGroupStatus,
    action: str,
):
    group, user = await _seed_group_user(async_session, status=from_status)
    with pytest.raises(ValueError) as exc:
        await error_group_service.transition_status(
            async_session, group, action=action, user_id=user.id,
            resolved_in_version_sha=None,
        )
    assert "illegal transition" in str(exc.value).lower()


async def test_resolve_sets_audit_fields(async_session: AsyncSession):
    group, user = await _seed_group_user(async_session, status=ErrorGroupStatus.OPEN)
    sha = "f" * 40
    updated = await error_group_service.transition_status(
        async_session, group, action="resolve", user_id=user.id,
        resolved_in_version_sha=sha,
    )
    assert updated.status == ErrorGroupStatus.RESOLVED
    assert updated.resolved_at is not None
    assert updated.resolved_by_user_id == user.id
    assert updated.resolved_in_version_sha == sha


async def test_reopen_clears_audit_fields(async_session: AsyncSession):
    group, user = await _seed_group_user(async_session, status=ErrorGroupStatus.OPEN)
    sha = "f" * 40
    await error_group_service.transition_status(
        async_session, group, action="resolve", user_id=user.id,
        resolved_in_version_sha=sha,
    )
    assert group.resolved_at is not None  # state 확인

    await error_group_service.transition_status(
        async_session, group, action="reopen", user_id=user.id,
        resolved_in_version_sha=None,
    )
    assert group.status == ErrorGroupStatus.OPEN
    assert group.resolved_at is None
    assert group.resolved_by_user_id is None
    assert group.resolved_in_version_sha is None


async def test_resolve_without_sha_keeps_field_none(async_session: AsyncSession):
    """resolved_in_version_sha 미제공 — None 으로 저장 (선택적)."""
    group, user = await _seed_group_user(async_session, status=ErrorGroupStatus.OPEN)
    updated = await error_group_service.transition_status(
        async_session, group, action="resolve", user_id=user.id,
        resolved_in_version_sha=None,
    )
    assert updated.status == ErrorGroupStatus.RESOLVED
    assert updated.resolved_in_version_sha is None
    assert updated.resolved_at is not None  # audit 필드는 sha 없어도 채움
    assert updated.resolved_by_user_id == user.id
