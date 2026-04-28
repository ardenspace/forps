"""phase1: logs + handoffs + git push events + project/task git fields

Revision ID: c4dee7f06004
Revises: be8724268ae4
Create Date: 2026-04-28 21:11:50.502585

설계서:
- docs/superpowers/specs/2026-04-26-ai-task-automation-design.md §4
- docs/superpowers/specs/2026-04-26-error-log-design.md §4

본 revision 은 단일 PR 머지를 의도. raw SQL 다수 사용 — alembic 자동 생성으로
표현 불가능한 부분(ALTER TYPE ADD VALUE / CHECK 정규식 / pg_trgm /
declarative partition / partial index).
"""
from typing import Sequence, Union
from datetime import datetime, timedelta

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c4dee7f06004'
down_revision: Union[str, None] = 'be8724268ae4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1) 기존 enum 확장: TaskEventAction ────────────────────────────
    # PostgreSQL ALTER TYPE ... ADD VALUE 는 트랜잭션 안에서 못 돌리므로
    # autocommit 블록으로 분리.
    with op.get_context().autocommit_block():
        for value in [
            "synced_from_plan",
            "checked_by_commit",
            "unchecked_by_commit",
            "archived_from_plan",
        ]:
            op.execute(f"ALTER TYPE taskeventaction ADD VALUE IF NOT EXISTS '{value}'")

    # 실패 복구 노트: 위 블록은 트랜잭션 외부에서 실행되므로 이후 블록이
    # 실패해도 enum 4값은 DB에 영구적으로 남는다. IF NOT EXISTS 가드 덕에
    # 재실행 안전하며, 잔존 값 자체는 기존 row 에 영향 없음 (PostgreSQL 은
    # ALTER TYPE DROP VALUE 미지원이라 downgrade 에서도 제거 불가).

    # ── 2) 신규 enum 타입 ───────────────────────────────────────────
    task_source = postgresql.ENUM(
        "manual", "synced_from_plan", name="tasksource", create_type=False
    )
    task_source.create(op.get_bind(), checkfirst=True)

    log_level = postgresql.ENUM(
        "debug", "info", "warning", "error", "critical",
        name="loglevel", create_type=False,
    )
    log_level.create(op.get_bind(), checkfirst=True)

    error_group_status = postgresql.ENUM(
        "open", "resolved", "ignored", "regressed",
        name="errorgroupstatus", create_type=False,
    )
    error_group_status.create(op.get_bind(), checkfirst=True)

    # ── 3) Project 6 컬럼 추가 ─────────────────────────────────────
    op.add_column("projects", sa.Column("git_repo_url", sa.String(), nullable=True))
    op.add_column(
        "projects",
        sa.Column("git_default_branch", sa.String(), nullable=False, server_default="main"),
    )
    op.add_column(
        "projects",
        sa.Column("plan_path", sa.String(), nullable=False, server_default="PLAN.md"),
    )
    op.add_column(
        "projects",
        sa.Column("handoff_dir", sa.String(), nullable=False, server_default="handoffs/"),
    )
    op.add_column("projects", sa.Column("last_synced_commit_sha", sa.String(), nullable=True))
    op.add_column(
        "projects", sa.Column("webhook_secret_encrypted", sa.LargeBinary(), nullable=True)
    )
    op.create_check_constraint(
        "ck_project_last_synced_commit_sha_format",
        "projects",
        "last_synced_commit_sha IS NULL OR last_synced_commit_sha ~ '^[0-9a-f]{40}$'",
    )

    # ── 4) Task 4 컬럼 + UNIQUE 부분 인덱스 + CHECK 제약 ──────────
    op.add_column(
        "tasks",
        sa.Column(
            "source",
            postgresql.ENUM("manual", "synced_from_plan", name="tasksource", create_type=False),
            nullable=False,
            server_default="manual",
        ),
    )
    op.add_column("tasks", sa.Column("external_id", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("last_commit_sha", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("archived_at", sa.DateTime(), nullable=True))

    op.create_index(
        "idx_task_project_external_id",
        "tasks",
        ["project_id", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )
    op.create_check_constraint(
        "ck_task_last_commit_sha_format",
        "tasks",
        "last_commit_sha IS NULL OR last_commit_sha ~ '^[0-9a-f]{40}$'",
    )

    # ── 5) Handoff ─────────────────────────────────────────────────
    op.create_table(
        "handoffs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("branch", sa.String(), nullable=False),
        sa.Column("author_user_id", sa.UUID(), nullable=True),
        sa.Column("author_git_login", sa.String(), nullable=False),
        sa.Column("commit_sha", sa.String(), nullable=False),
        sa.Column("pushed_at", sa.DateTime(), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("parsed_tasks", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("free_notes", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "commit_sha", name="uq_handoff_project_commit"),
        sa.CheckConstraint(
            "commit_sha ~ '^[0-9a-f]{40}$'",
            name="ck_handoff_commit_sha_format",
        ),
    )

    # ── 6) GitPushEvent ────────────────────────────────────────────
    op.create_table(
        "git_push_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("branch", sa.String(), nullable=False),
        sa.Column("head_commit_sha", sa.String(), nullable=False),
        sa.Column("commits", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "commits_truncated", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("pusher", sa.String(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "head_commit_sha", name="uq_git_push_project_head"
        ),
        sa.CheckConstraint(
            "head_commit_sha ~ '^[0-9a-f]{40}$'",
            name="ck_git_push_head_commit_sha_format",
        ),
    )

    # ── 7) LogIngestToken ──────────────────────────────────────────
    op.create_table(
        "log_ingest_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("secret_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column(
            "rate_limit_per_minute", sa.Integer(), nullable=False, server_default="600"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── 8) RateLimitWindow (composite PK) ─────────────────────────
    op.create_table(
        "rate_limit_windows",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("token_id", sa.UUID(), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["token_id"], ["log_ingest_tokens.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "project_id", "token_id", "window_start", name="pk_rate_limit_window"
        ),
    )

    # ── 9) ErrorGroup ──────────────────────────────────────────────
    op.create_table(
        "error_groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("exception_class", sa.String(), nullable=False),
        sa.Column("exception_message_sample", sa.Text(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("first_seen_version_sha", sa.String(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_version_sha", sa.String(), nullable=False),
        sa.Column(
            "event_count", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "open", "resolved", "ignored", "regressed",
                name="errorgroupstatus", create_type=False,
            ),
            nullable=False,
            server_default="open",
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_user_id", sa.UUID(), nullable=True),
        sa.Column("resolved_in_version_sha", sa.String(), nullable=True),
        sa.Column("last_alerted_new_at", sa.DateTime(), nullable=True),
        sa.Column("last_alerted_spike_at", sa.DateTime(), nullable=True),
        sa.Column("last_alerted_regression_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "fingerprint", name="uq_error_group_project_fingerprint"
        ),
        sa.CheckConstraint(
            "first_seen_version_sha ~ '^[0-9a-f]{40}$' OR first_seen_version_sha = 'unknown'",
            name="ck_error_group_first_sha_format",
        ),
        sa.CheckConstraint(
            "last_seen_version_sha ~ '^[0-9a-f]{40}$' OR last_seen_version_sha = 'unknown'",
            name="ck_error_group_last_sha_format",
        ),
        sa.CheckConstraint(
            "resolved_in_version_sha IS NULL OR resolved_in_version_sha ~ '^[0-9a-f]{40}$'",
            name="ck_error_group_resolved_sha_format",
        ),
    )

    # ── 10) pg_trgm extension ─────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── 11) LogEvent (declarative partition by received_at) ──────
    op.execute("""
        CREATE TABLE log_events (
            id            UUID NOT NULL,
            project_id    UUID NOT NULL,
            level         loglevel NOT NULL,
            message       TEXT NOT NULL,
            logger_name   TEXT NOT NULL,
            version_sha   TEXT NOT NULL,
            environment   TEXT NOT NULL,
            hostname      TEXT NOT NULL,
            emitted_at    TIMESTAMP NOT NULL,
            received_at   TIMESTAMP NOT NULL,
            exception_class    TEXT,
            exception_message  TEXT,
            stack_trace        TEXT,
            stack_frames       JSON,
            fingerprint        TEXT,
            fingerprinted_at   TIMESTAMP,
            user_id_external   TEXT,
            request_id         TEXT,
            extra              JSON,
            PRIMARY KEY (id, received_at),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            CHECK (version_sha ~ '^[0-9a-f]{40}$' OR version_sha = 'unknown')
        ) PARTITION BY RANGE (received_at)
    """)

    # ── 12) 인덱스 5종 ─────────────────────────────────────────────
    op.create_index(
        "idx_log_project_level_received",
        "log_events",
        ["project_id", "level", sa.text("received_at DESC")],
    )
    op.create_index(
        "idx_log_fingerprint",
        "log_events",
        ["project_id", "fingerprint"],
        postgresql_where=sa.text("fingerprint IS NOT NULL"),
    )
    op.create_index(
        "idx_log_version_sha",
        "log_events",
        ["project_id", "version_sha"],
    )
    op.create_index(
        "idx_log_unfingerprinted",
        "log_events",
        ["project_id", "id"],
        postgresql_where=sa.text(
            "level IN ('error','critical') AND fingerprinted_at IS NULL"
        ),
    )
    op.execute("""
        CREATE INDEX idx_log_message_trgm
          ON log_events USING gin (message gin_trgm_ops)
          WHERE level IN ('warning','error','critical')
    """)

    # ── 13) 30일치 daily partition pre-create ─────────────────────
    today = datetime.utcnow().date()
    for day_offset in range(31):
        d = today + timedelta(days=day_offset)
        next_d = d + timedelta(days=1)
        partition_name = f"log_events_{d.strftime('%Y%m%d')}"
        op.execute(f"""
            CREATE TABLE {partition_name} PARTITION OF log_events
              FOR VALUES FROM ('{d.isoformat()}') TO ('{next_d.isoformat()}')
        """)


def downgrade() -> None:
    # 13) daily partition + log_events
    today = datetime.utcnow().date()
    for day_offset in range(31):
        d = today + timedelta(days=day_offset)
        partition_name = f"log_events_{d.strftime('%Y%m%d')}"
        op.execute(f"DROP TABLE IF EXISTS {partition_name}")
    op.execute("DROP INDEX IF EXISTS idx_log_message_trgm")
    op.drop_index("idx_log_unfingerprinted", table_name="log_events")
    op.drop_index("idx_log_version_sha", table_name="log_events")
    op.drop_index("idx_log_fingerprint", table_name="log_events")
    op.drop_index("idx_log_project_level_received", table_name="log_events")
    op.execute("DROP TABLE IF EXISTS log_events")
    # pg_trgm 은 다른 곳에서 쓸 수도 있으므로 굳이 DROP 하지 않음.

    # 9) ErrorGroup
    op.drop_table("error_groups")

    # 8) RateLimitWindow
    op.drop_table("rate_limit_windows")

    # 7) LogIngestToken
    op.drop_table("log_ingest_tokens")

    # 6) GitPushEvent
    op.drop_table("git_push_events")

    # 5) Handoff
    op.drop_table("handoffs")

    # 4) Task — CHECK + 부분 인덱스 + 4 컬럼
    op.drop_constraint("ck_task_last_commit_sha_format", "tasks", type_="check")
    op.drop_index("idx_task_project_external_id", table_name="tasks")
    op.drop_column("tasks", "archived_at")
    op.drop_column("tasks", "last_commit_sha")
    op.drop_column("tasks", "external_id")
    op.drop_column("tasks", "source")

    # 3) Project — CHECK + 6 컬럼
    op.drop_constraint("ck_project_last_synced_commit_sha_format", "projects", type_="check")
    op.drop_column("projects", "webhook_secret_encrypted")
    op.drop_column("projects", "last_synced_commit_sha")
    op.drop_column("projects", "handoff_dir")
    op.drop_column("projects", "plan_path")
    op.drop_column("projects", "git_default_branch")
    op.drop_column("projects", "git_repo_url")

    # 2) 신규 enum 타입
    op.execute("DROP TYPE IF EXISTS errorgroupstatus")
    op.execute("DROP TYPE IF EXISTS loglevel")
    op.execute("DROP TYPE IF EXISTS tasksource")

    # 1) TaskEventAction 4값 — PostgreSQL ALTER TYPE DROP VALUE 미지원.
    # 4 enum 값이 downgrade 후에도 남는다. 새 row 가 enum 값을 사용하지
    # 않았다면 무해. 사용했다면 downgrade 자체가 부적절한 상황.
    # 운영 노트: Phase 1 downgrade 가 필요하면 사전에 row 정리 필요.
