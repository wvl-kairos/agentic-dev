"""add_initial_interview_stage

Revision ID: d1e2f3a4b5c6
Revises: c7a3f1d8e902
Create Date: 2026-03-06 17:30:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c7a3f1d8e902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL ALTER TYPE ... ADD VALUE cannot run inside a transaction
    op.execute("ALTER TYPE interviewtype ADD VALUE IF NOT EXISTS 'initial' BEFORE 'screening'")
    op.execute("ALTER TYPE pipelinestage ADD VALUE IF NOT EXISTS 'initial_interview' BEFORE 'screening'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums.
    # To reverse, you would need to recreate the enum type without the value.
    pass
