"""add_check_constraint_on_content_candidates

Revision ID: 6b86727525d3
Revises: 20ae84738be2
Create Date: 2026-10-05 09:32:50.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6b86727525d3'
down_revision: Union[str, Sequence[str], None] = '20ae84738be2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table('content_candidates', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_content_candidate_status',
            "status IN ('draft', 'pending_approval', 'approved', 'rejected', 'published')"
        )

def downgrade() -> None:
    with op.batch_alter_table('content_candidates', schema=None) as batch_op:
        batch_op.drop_constraint('ck_content_candidate_status', type_='check')
