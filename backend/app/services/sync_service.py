"""webhook GitPushEvent → DB 반영 조립 서비스.

설계서: 2026-04-26-ai-task-automation-design.md §5.1 (⑤), §7.1

흐름:
  1) processed_at 가드 — 이미 처리된 이벤트는 즉시 종료 (멱등성)
  2) 변경 파일 목록 결정 — commits_truncated 시 Compare API, 아니면 commits[*].modified
  3) PLAN/handoff 매칭 — 둘 다 없으면 sync 종료 (processed_at = now)
  4) git_repo_service 로 head_sha 기준 raw fetch
  5) plan_parser_service / handoff_parser_service 호출
  6) DB 반영: Task status / archived_at / Handoff INSERT / TaskEvent
  7) processed_at = now (성공/실패 모두). 실패면 error 도 기록.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_push_event import GitPushEvent
from app.models.project import Project

logger = logging.getLogger(__name__)


FetchFile = Callable[[str, str | None, str, str], Awaitable[str | None]]
FetchCompare = Callable[[str, str | None, str, str], Awaitable[list[str]]]


async def process_event(
    db: AsyncSession,
    event: GitPushEvent,
    *,
    fetch_file: FetchFile,
    fetch_compare: FetchCompare,
) -> None:
    """진입점. 멱등 + 결정적 — 같은 event 두 번 호출해도 DB 변경 1회만."""
    if event.processed_at is not None:
        logger.info("event %s already processed at %s — skip", event.id, event.processed_at)
        return

    project = await db.get(Project, event.project_id)
    if project is None:
        event.processed_at = datetime.utcnow()
        event.error = "project not found"
        await db.commit()
        return

    event_id = event.id  # 세션 poison 후 expire 대비

    try:
        await _process_inner(db, event, project, fetch_file=fetch_file, fetch_compare=fetch_compare)
        event.processed_at = datetime.utcnow()
        await db.commit()
    except Exception as exc:
        # I-2 fix: _process_inner 내부에서 예외 발생 시 세션이 poisoned 상태일 수 있음.
        # rollback → SQLAlchemy 가 pending/new 객체를 identity map 에서 자동 제거.
        # event 는 persistent 상태로 남음. autoflush=False 로 commit 전 autoflush 유발 방지.
        logger.exception("sync failed for event %s", event_id)
        try:
            await db.rollback()
        except Exception:
            pass
        db.sync_session.autoflush = False
        now = datetime.utcnow()
        error_msg = f"{type(exc).__name__}: {exc}"
        event.processed_at = now
        event.error = error_msg
        await db.commit()
        db.sync_session.autoflush = True


async def _process_inner(
    db: AsyncSession,
    event: GitPushEvent,
    project: Project,
    *,
    fetch_file: FetchFile,
    fetch_compare: FetchCompare,
) -> None:
    changed_files = await _collect_changed_files(
        event, project, fetch_compare=fetch_compare
    )
    plan_changed = project.plan_path in changed_files
    handoff_path = _handoff_file_path(project, event.branch)
    handoff_changed = handoff_path in changed_files

    if not plan_changed and not handoff_changed:
        logger.info("event %s: no PLAN/handoff in changed files — skip", event.id)
        return

    pat = _decrypt_pat(project)

    if plan_changed and project.git_repo_url is not None:
        plan_text = await fetch_file(
            project.git_repo_url, pat, event.head_commit_sha, project.plan_path
        )
        if plan_text is not None:
            await _apply_plan(db, project, event, plan_text)
        else:
            logger.info("event %s: PLAN.md returned 404 — skip plan", event.id)

    if handoff_changed and project.git_repo_url is not None:
        handoff_text = await fetch_file(
            project.git_repo_url, pat, event.head_commit_sha, handoff_path
        )
        if handoff_text is not None:
            await _apply_handoff(db, project, event, handoff_text)
        else:
            logger.warning(
                "event %s: handoff %s returned 404 — skip", event.id, handoff_path
            )


def _handoff_file_path(project: Project, branch: str) -> str:
    """`handoff_dir + branch.replace('/', '-') + '.md'`. 설계서 §6.2 위치 규약."""
    base = project.handoff_dir if project.handoff_dir.endswith("/") else project.handoff_dir + "/"
    return base + branch.replace("/", "-") + ".md"


async def _collect_changed_files(
    event: GitPushEvent,
    project: Project,
    *,
    fetch_compare: FetchCompare,
) -> set[str]:
    """변경 파일 결정. commits_truncated 시 Compare API 호출.

    - truncated == False: commits[*].modified ∪ commits[*].added 합집합
    - truncated == True: Compare API. base = project.last_synced_commit_sha or commits[-1].id (fallback)
    """
    if not event.commits_truncated:
        files: set[str] = set()
        for c in event.commits or []:
            files.update(c.get("modified") or [])
            files.update(c.get("added") or [])
        return files

    if project.git_repo_url is None:
        return set()

    base = event.before_commit_sha
    # GitHub null-sha (`0` * 40) → "no prior commit", fall through to next priority
    if base == "0" * 40:
        base = None
    if base is None:
        base = project.last_synced_commit_sha
    if base is None and event.commits:
        base = event.commits[-1].get("id") or event.head_commit_sha
    if base is None:
        base = event.head_commit_sha

    pat = _decrypt_pat(project)
    files_list = await fetch_compare(project.git_repo_url, pat, base, event.head_commit_sha)
    return set(files_list)


def _decrypt_pat(project: Project) -> str | None:
    if project.github_pat_encrypted is None:
        return None
    from app.core.crypto import decrypt_secret

    try:
        return decrypt_secret(project.github_pat_encrypted)
    except Exception:
        logger.exception("failed to decrypt PAT for project %s", project.id)
        return None


async def _apply_plan(
    db: AsyncSession,
    project: Project,
    event: GitPushEvent,
    plan_text: str,
) -> None:
    """PLAN.md 파싱 → Task INSERT/UPDATE + archived_at."""
    from sqlalchemy import select

    from app.models.task import Task, TaskSource, TaskStatus
    from app.models.task_event import TaskEvent, TaskEventAction
    from app.services.plan_parser_service import parse_plan

    parsed = parse_plan(plan_text)  # DuplicateExternalIdError 는 process_event 가 catch

    rows = (await db.execute(
        select(Task).where(
            Task.project_id == project.id,
            Task.source == TaskSource.SYNCED_FROM_PLAN,
        )
    )).scalars().all()
    existing: dict[str, Task] = {t.external_id: t for t in rows if t.external_id}

    for parsed_task in parsed.tasks:
        existing_task = existing.get(parsed_task.external_id)
        new_status = TaskStatus.DONE if parsed_task.checked else TaskStatus.TODO

        if existing_task is None:
            t = Task(
                project_id=project.id,
                title=parsed_task.title,
                source=TaskSource.SYNCED_FROM_PLAN,
                external_id=parsed_task.external_id,
                status=new_status,
                last_commit_sha=event.head_commit_sha,
            )
            db.add(t)
            await db.flush()
            db.add(TaskEvent(
                task_id=t.id,
                action=TaskEventAction.SYNCED_FROM_PLAN,
                changes={
                    "external_id": parsed_task.external_id,
                    "title": parsed_task.title,
                    "checked": parsed_task.checked,
                },
            ))
        else:
            previous_status = existing_task.status
            # I-1 fix: archived 였으면 un-archive (재 INSERT 아님 — 히스토리 보존)
            if existing_task.archived_at is not None:
                existing_task.archived_at = None
                # un-archive 자체는 status 변경 없음 — 아래 status 전이 규칙이 그대로 적용됨
            if parsed_task.checked and previous_status != TaskStatus.DONE:
                existing_task.status = TaskStatus.DONE
                existing_task.last_commit_sha = event.head_commit_sha
                db.add(TaskEvent(
                    task_id=existing_task.id,
                    action=TaskEventAction.CHECKED_BY_COMMIT,
                    changes={
                        "previous_status": previous_status.value,
                        "commit_sha": event.head_commit_sha,
                    },
                ))
            elif not parsed_task.checked and previous_status == TaskStatus.DONE:
                existing_task.status = TaskStatus.TODO
                existing_task.last_commit_sha = event.head_commit_sha
                db.add(TaskEvent(
                    task_id=existing_task.id,
                    action=TaskEventAction.UNCHECKED_BY_COMMIT,
                    changes={
                        "previous_status": previous_status.value,
                        "commit_sha": event.head_commit_sha,
                    },
                ))
            # else: 변경 없음 — last_commit_sha 도 안 바꿈

    parsed_ids = {t.external_id for t in parsed.tasks}
    for ext_id, task in existing.items():
        if ext_id not in parsed_ids and task.archived_at is None:
            task.archived_at = datetime.utcnow()
            db.add(TaskEvent(
                task_id=task.id,
                action=TaskEventAction.ARCHIVED_FROM_PLAN,
                changes={
                    "external_id": ext_id,
                    "commit_sha": event.head_commit_sha,
                },
            ))


async def _apply_handoff(
    db: AsyncSession,
    project: Project,
    event: GitPushEvent,
    handoff_text: str,
) -> None:
    """handoff 파싱 → Handoff INSERT (UNIQUE 멱등) + raw_content 저장.

    parsed_tasks 는 sections[0].checks (active 섹션). free_notes 는 sections[0] 의
    free_notes + subtasks 합본. 다중 날짜 history 는 raw_content 에 보존.
    """
    from sqlalchemy.exc import IntegrityError

    from app.models.handoff import Handoff
    from app.services.handoff_parser_service import parse_handoff

    parsed = parse_handoff(handoff_text)
    if not parsed.sections:
        return

    active = parsed.sections[0]
    parsed_tasks = [
        {"external_id": c.external_id, "checked": c.checked, "extra": c.extra}
        for c in active.checks
    ]
    free_notes = {
        "last_commit": active.free_notes.last_commit,
        "next": active.free_notes.next,
        "blockers": active.free_notes.blockers,
        "subtasks": [
            {
                "parent_external_id": s.parent_external_id,
                "checked": s.checked,
                "text": s.text,
            }
            for s in active.subtasks
        ],
    }

    handoff = Handoff(
        project_id=project.id,
        branch=parsed.branch,
        author_git_login=parsed.author_git_login,
        commit_sha=event.head_commit_sha,
        pushed_at=event.received_at,
        raw_content=handoff_text,
        parsed_tasks=parsed_tasks,
        free_notes=free_notes,
    )
    try:
        async with db.begin_nested():
            db.add(handoff)
            await db.flush()
    except IntegrityError:
        logger.info(
            "handoff already exists for project=%s commit=%s — skip",
            project.id, event.head_commit_sha,
        )
