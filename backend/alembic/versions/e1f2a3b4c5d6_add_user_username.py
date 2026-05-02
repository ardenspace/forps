"""add_user_username

Revision ID: e1f2a3b4c5d6
Revises: 7c6e0c9bb915
Create Date: 2026-05-02 10:00:00.000000

User.username — `@username` mention 매핑용. nullable + unique + indexed.
backfill 안 함 — 신규 사용자는 가입 후 settings 에서 직접 설정.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = '7c6e0c9bb915'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
