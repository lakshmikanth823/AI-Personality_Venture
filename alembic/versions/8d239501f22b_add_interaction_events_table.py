"""add_interaction_events_table

Revision ID: 8d239501f22b
Revises: 7c128490e11a
Create Date: 2026-10-05 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8d239501f22b'
down_revision: Union[str, Sequence[str], None] = '7c128490e11a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if 'interaction_events' not in insp.get_table_names():
        op.create_table(
            'interaction_events',
            sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
            sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('event_type', sa.String(length=64), nullable=False),
            sa.Column('variant_id', sa.String(length=64), nullable=True),
            sa.Column('platform', sa.String(length=32), nullable=False, server_default='web'),
            sa.Column('metadata_json', sa.Text(), server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_interaction_events_id', 'interaction_events', ['id'], unique=False)
        op.create_index('ix_interaction_events_user_id', 'interaction_events', ['user_id'], unique=False)
        op.create_index('ix_interaction_events_event_type', 'interaction_events', ['event_type'], unique=False)
        op.create_index('ix_interaction_events_variant_id', 'interaction_events', ['variant_id'], unique=False)
        op.create_index('ix_interaction_events_created_at', 'interaction_events', ['created_at'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_interaction_events_created_at', table_name='interaction_events')
    op.drop_index('ix_interaction_events_variant_id', table_name='interaction_events')
    op.drop_index('ix_interaction_events_event_type', table_name='interaction_events')
    op.drop_index('ix_interaction_events_user_id', table_name='interaction_events')
    op.drop_index('ix_interaction_events_id', table_name='interaction_events')
    op.drop_table('interaction_events')
