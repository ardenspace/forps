"""sync_service — webhook 이벤트 → DB 반영 통합 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §5.1 (⑤), §7.1, §10.2
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_push_event import GitPushEvent
from app.models.handoff import Handoff
from app.models.project import Project
from app.models.task import Task, TaskSource, TaskStatus
from app.models.task_event import TaskEvent, TaskEventAction
from app.models.workspace import Workspace
from app.services.sync_service import process_event


async def _seed_project(
    db: AsyncSession, *, repo_url: str | None = "https://github.com/ardenspace/app-chak"
) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p", git_repo_url=repo_url)
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def _seed_event(
    db: AsyncSession,
    project: Project,
    *,
    head_sha: str = "a" * 40,
    branch: str = "main",
    commits: list[dict] | None = None,
    commits_truncated: bool = False,
    processed_at: datetime | None = None,
) -> GitPushEvent:
    event = GitPushEvent(
        project_id=project.id,
        branch=branch,
        head_commit_sha=head_sha,
        commits=commits or [],
        commits_truncated=commits_truncated,
        pusher="alice",
        processed_at=processed_at,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def _noop_fetch_file(repo_url: str, pat: str | None, sha: str, path: str) -> str | None:
    return None


async def _noop_fetch_compare(repo_url: str, pat: str | None, base: str, head: str) -> list[str]:
    return []


async def test_process_event_skips_already_processed(async_session: AsyncSession):
    """processed_at IS NOT NULL 이면 즉시 종료 — DB 변경 없음."""
    proj = await _seed_project(async_session)
    event = await _seed_event(
        async_session, proj, processed_at=datetime.utcnow() - timedelta(minutes=10)
    )
    initial_processed_at = event.processed_at

    await process_event(
        async_session, event,
        fetch_file=_noop_fetch_file, fetch_compare=_noop_fetch_compare,
    )

    await async_session.refresh(event)
    assert event.processed_at == initial_processed_at
    assert event.error is None


async def test_process_event_marks_processed_when_no_relevant_files(
    async_session: AsyncSession,
):
    """변경 파일 중 PLAN/handoff 없음 → fetch 안 함, processed_at = now()."""
    proj = await _seed_project(async_session)
    event = await _seed_event(
        async_session, proj,
        commits=[{"modified": ["frontend/Button.tsx"], "added": [], "removed": []}],
    )

    await process_event(
        async_session, event,
        fetch_file=_noop_fetch_file, fetch_compare=_noop_fetch_compare,
    )

    await async_session.refresh(event)
    assert event.processed_at is not None
    assert event.error is None


async def test_process_event_creates_new_tasks_from_plan(async_session: AsyncSession):
    """PLAN 에 새 task-XXX 가 있으면 Task INSERT (source=SYNCED_FROM_PLAN, status 매핑)."""
    proj = await _seed_project(async_session)
    plan_text = """# 스프린트: 2026-04

## 태스크

- [ ] [task-001] 새 작업 — @alice
- [x] [task-002] 이미 완료 — @bob
"""

    async def fake_fetch_file(repo_url, pat, sha, path):
        if path == "PLAN.md":
            return plan_text
        return None

    event = await _seed_event(
        async_session, proj,
        commits=[{"modified": ["PLAN.md"], "added": [], "removed": []}],
    )

    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )

    await async_session.refresh(event)
    assert event.processed_at is not None
    assert event.error is None

    rows = (
        await async_session.execute(
            select(Task).where(Task.project_id == proj.id).order_by(Task.external_id)
        )
    ).scalars().all()
    assert len(rows) == 2
    t1 = next(t for t in rows if t.external_id == "task-001")
    t2 = next(t for t in rows if t.external_id == "task-002")
    assert t1.source == TaskSource.SYNCED_FROM_PLAN
    assert t1.status == TaskStatus.TODO
    assert t1.title == "새 작업"
    assert t1.last_commit_sha == event.head_commit_sha
    assert t2.status == TaskStatus.DONE
    assert t2.last_commit_sha == event.head_commit_sha


async def test_process_event_records_synced_from_plan_event(async_session: AsyncSession):
    """신규 Task INSERT 시 TaskEvent(action=SYNCED_FROM_PLAN) 도 만들어짐."""
    proj = await _seed_project(async_session)
    plan_text = "## 태스크\n\n- [ ] [task-100] 신규 — @alice\n"

    async def fake_fetch_file(repo_url, pat, sha, path):
        return plan_text if path == "PLAN.md" else None

    event = await _seed_event(
        async_session, proj, commits=[{"modified": ["PLAN.md"]}]
    )
    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )

    task = (await async_session.execute(
        select(Task).where(Task.external_id == "task-100")
    )).scalar_one()
    events = (await async_session.execute(
        select(TaskEvent).where(TaskEvent.task_id == task.id)
    )).scalars().all()
    assert any(e.action == TaskEventAction.SYNCED_FROM_PLAN for e in events)


async def test_process_event_skips_when_plan_404(async_session: AsyncSession):
    """fetch_file 이 None (404) 반환 → sync 종료, error 기록 없음."""
    proj = await _seed_project(async_session)

    async def fake_fetch_file(repo_url, pat, sha, path):
        return None

    event = await _seed_event(
        async_session, proj, commits=[{"modified": ["PLAN.md"]}]
    )
    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )

    await async_session.refresh(event)
    assert event.processed_at is not None
    assert event.error is None
    rows = (await async_session.execute(
        select(Task).where(Task.project_id == proj.id)
    )).scalars().all()
    assert rows == []


async def test_process_event_checks_existing_task_to_done(async_session: AsyncSession):
    """기존 TODO task 가 PLAN 에서 [x] 로 → DONE + CHECKED_BY_COMMIT TaskEvent."""
    proj = await _seed_project(async_session)
    existing = Task(
        project_id=proj.id,
        title="기존",
        source=TaskSource.SYNCED_FROM_PLAN,
        external_id="task-001",
        status=TaskStatus.TODO,
    )
    async_session.add(existing)
    await async_session.commit()
    await async_session.refresh(existing)

    plan_text = "## 태스크\n\n- [x] [task-001] 기존 — @alice\n"

    async def fake_fetch_file(repo_url, pat, sha, path):
        return plan_text if path == "PLAN.md" else None

    event = await _seed_event(
        async_session, proj, commits=[{"modified": ["PLAN.md"]}]
    )
    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )
    await async_session.refresh(existing)

    assert existing.status == TaskStatus.DONE
    assert existing.last_commit_sha == event.head_commit_sha
    events = (await async_session.execute(
        select(TaskEvent).where(TaskEvent.task_id == existing.id)
    )).scalars().all()
    assert any(e.action == TaskEventAction.CHECKED_BY_COMMIT for e in events)


async def test_process_event_rolls_back_done_to_todo(async_session: AsyncSession):
    """직전 DONE 인 task 가 PLAN 에서 [ ] 로 → TODO + UNCHECKED_BY_COMMIT."""
    proj = await _seed_project(async_session)
    existing = Task(
        project_id=proj.id,
        title="롤백 케이스",
        source=TaskSource.SYNCED_FROM_PLAN,
        external_id="task-002",
        status=TaskStatus.DONE,
    )
    async_session.add(existing)
    await async_session.commit()
    await async_session.refresh(existing)

    plan_text = "## 태스크\n\n- [ ] [task-002] 롤백 케이스\n"

    async def fake_fetch_file(repo_url, pat, sha, path):
        return plan_text if path == "PLAN.md" else None

    event = await _seed_event(
        async_session, proj, commits=[{"modified": ["PLAN.md"]}]
    )
    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )
    await async_session.refresh(existing)

    assert existing.status == TaskStatus.TODO
    events = (await async_session.execute(
        select(TaskEvent).where(TaskEvent.task_id == existing.id)
    )).scalars().all()
    assert any(e.action == TaskEventAction.UNCHECKED_BY_COMMIT for e in events)


async def test_process_event_no_change_when_unchecked_and_already_not_done(
    async_session: AsyncSession,
):
    """직전 TODO 인 task 가 PLAN 에서 [ ] → 변경 없음, TaskEvent 도 안 만듦."""
    proj = await _seed_project(async_session)
    existing = Task(
        project_id=proj.id,
        title="변경 없음",
        source=TaskSource.SYNCED_FROM_PLAN,
        external_id="task-003",
        status=TaskStatus.DOING,
    )
    async_session.add(existing)
    await async_session.commit()
    await async_session.refresh(existing)

    plan_text = "## 태스크\n\n- [ ] [task-003] 변경 없음\n"

    async def fake_fetch_file(repo_url, pat, sha, path):
        return plan_text if path == "PLAN.md" else None

    event = await _seed_event(
        async_session, proj, commits=[{"modified": ["PLAN.md"]}]
    )
    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )
    await async_session.refresh(existing)

    assert existing.status == TaskStatus.DOING
    events = (await async_session.execute(
        select(TaskEvent).where(TaskEvent.task_id == existing.id)
    )).scalars().all()
    assert len(events) == 0


async def test_process_event_archives_tasks_removed_from_plan(async_session: AsyncSession):
    """기존 synced task 가 새 PLAN 에 없으면 archived_at = now() + ARCHIVED_FROM_PLAN."""
    proj = await _seed_project(async_session)
    keep = Task(
        project_id=proj.id, title="유지", source=TaskSource.SYNCED_FROM_PLAN,
        external_id="task-001", status=TaskStatus.TODO,
    )
    removed = Task(
        project_id=proj.id, title="삭제됨", source=TaskSource.SYNCED_FROM_PLAN,
        external_id="task-OLD", status=TaskStatus.DOING,
    )
    async_session.add_all([keep, removed])
    await async_session.commit()
    await async_session.refresh(removed)

    plan_text = "## 태스크\n\n- [ ] [task-001] 유지\n"

    async def fake_fetch_file(repo_url, pat, sha, path):
        return plan_text if path == "PLAN.md" else None

    event = await _seed_event(
        async_session, proj, commits=[{"modified": ["PLAN.md"]}]
    )
    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )
    await async_session.refresh(removed)
    await async_session.refresh(keep)

    assert removed.archived_at is not None
    assert keep.archived_at is None
    events = (await async_session.execute(
        select(TaskEvent).where(TaskEvent.task_id == removed.id)
    )).scalars().all()
    assert any(e.action == TaskEventAction.ARCHIVED_FROM_PLAN for e in events)


async def test_process_event_does_not_archive_manual_tasks(async_session: AsyncSession):
    """source=MANUAL 인 task 는 PLAN 에 없어도 archived_at 안 변경."""
    proj = await _seed_project(async_session)
    manual = Task(
        project_id=proj.id, title="수동", source=TaskSource.MANUAL,
        external_id=None, status=TaskStatus.TODO,
    )
    async_session.add(manual)
    await async_session.commit()
    await async_session.refresh(manual)

    plan_text = "## 태스크\n\n- [ ] [task-001] PLAN 만\n"

    async def fake_fetch_file(repo_url, pat, sha, path):
        return plan_text if path == "PLAN.md" else None

    event = await _seed_event(
        async_session, proj, commits=[{"modified": ["PLAN.md"]}]
    )
    await process_event(
        async_session, event,
        fetch_file=fake_fetch_file, fetch_compare=_noop_fetch_compare,
    )
    await async_session.refresh(manual)
    assert manual.archived_at is None
