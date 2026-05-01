"""phase6_discord_counter

Revision ID: 7c6e0c9bb915
Revises: a1b2c3d4e5f6
Create Date: 2026-05-01 11:25:09.216965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c6e0c9bb915'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 6 — Discord 알림 auto-disable 추적 컬럼 추가
    op.add_column('projects', sa.Column(
        'discord_consecutive_failures', sa.Integer(),
        nullable=False, server_default='0',
    ))
    op.add_column('projects', sa.Column(
        'discord_disabled_at', sa.DateTime(), nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('projects', 'discord_disabled_at')
    op.drop_column('projects', 'discord_consecutive_failures')
