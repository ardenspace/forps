"""phase4: project github_pat_encrypted column

Revision ID: 274c0ed55105
Revises: c4dee7f06004
Create Date: 2026-04-29 00:00:00.000000

설계서:
- docs/superpowers/specs/2026-04-26-ai-task-automation-design.md §9 (GitHub PAT Fernet 암호화 저장)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '274c0ed55105'
down_revision: Union[str, None] = 'c4dee7f06004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('github_pat_encrypted', sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'github_pat_encrypted')
