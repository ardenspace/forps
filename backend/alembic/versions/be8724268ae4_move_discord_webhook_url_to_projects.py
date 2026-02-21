"""move discord_webhook_url from workspaces to projects

Revision ID: be8724268ae4
Revises: f505ff961917
Create Date: 2026-02-21 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'be8724268ae4'
down_revision: Union[str, None] = 'f505ff961917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('discord_webhook_url', sa.String(), nullable=True))
    op.drop_column('workspaces', 'discord_webhook_url')


def downgrade() -> None:
    op.add_column('workspaces', sa.Column('discord_webhook_url', sa.String(), nullable=True))
    op.drop_column('projects', 'discord_webhook_url')
