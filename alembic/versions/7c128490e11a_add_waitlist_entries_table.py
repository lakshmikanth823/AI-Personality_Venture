"""add_waitlist_entries_table

Revision ID: 7c128490e11a
Revises: 6b86727525d3
Create Date: 2026-10-05 10:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '7c128490e11a'
down_revision: Union[str, Sequence[str], None] = '6b86727525d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if 'waitlist_entries' not in insp.get_table_names():
        op.create_table(
            'waitlist_entries',
            sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=32), nullable=True),
            sa.Column('queue_position', sa.Integer(), nullable=False),
            sa.Column('referral_code', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='waiting'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_waitlist_entries_id', 'waitlist_entries', ['id'], unique=False)
        op.create_index('ix_waitlist_entries_email', 'waitlist_entries', ['email'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_waitlist_entries_email', table_name='waitlist_entries')
    op.drop_index('ix_waitlist_entries_id', table_name='waitlist_entries')
    op.drop_table('waitlist_entries')
