"""phase5a: gitpushevent before_commit_sha column

Revision ID: a1b2c3d4e5f6
Revises: 274c0ed55105
Create Date: 2026-04-29 00:00:00.000000

설계서:
- docs/superpowers/plans/2026-04-29-phase-2-webhook-receive.md
- Phase 5a: commits_truncated base 정확화 (webhook payload 의 `before` 필드 보존)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '274c0ed55105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('git_push_events', sa.Column('before_commit_sha', sa.String(), nullable=True))
    op.create_check_constraint(
        'ck_git_push_event_before_sha_hex',
        'git_push_events',
        "before_commit_sha IS NULL OR before_commit_sha ~ '^[0-9a-f]{40}$'",
    )


def downgrade() -> None:
    op.drop_constraint('ck_git_push_event_before_sha_hex', 'git_push_events', type_='check')
    op.drop_column('git_push_events', 'before_commit_sha')
