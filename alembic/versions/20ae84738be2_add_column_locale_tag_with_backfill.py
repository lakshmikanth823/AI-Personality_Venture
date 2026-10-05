"""add_column_locale_tag_with_backfill

Revision ID: 20ae84738be2
Revises: a1c31c7dd9aa
Create Date: 2026-10-05 09:32:43.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20ae84738be2'
down_revision: Union[str, Sequence[str], None] = 'a1c31c7dd9aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locale_tag', sa.String(length=16), nullable=True))

    # Real data backfill for existing rows
    op.execute("UPDATE profiles SET locale_tag = 'en_IN' WHERE locale_tag IS NULL")

def downgrade() -> None:
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.drop_column('locale_tag')
