"""add_index_on_messages_created_at

Revision ID: a1c31c7dd9aa
Revises: 364a0d60c198
Create Date: 2026-10-05 09:32:38.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1c31c7dd9aa'
down_revision: Union[str, Sequence[str], None] = '364a0d60c198'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.create_index('ix_messages_created_at', ['created_at'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index('ix_messages_created_at')
