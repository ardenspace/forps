"""add discord_webhook_url to workspaces

Revision ID: f505ff961917
Revises: d48a0b63f867
Create Date: 2026-02-21 21:44:38.884277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f505ff961917'
down_revision: Union[str, None] = 'd48a0b63f867'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('workspaces', sa.Column('discord_webhook_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('workspaces', 'discord_webhook_url')
