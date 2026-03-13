"""Phase 3: add orientation field to candidates

Add orientation VARCHAR(20) to candidates table.
Values: frontend, backend, fullstack, data, devops.
Nullable, computed during assessment pipeline.

Revision ID: g4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-03-13
"""

from alembic import op
import sqlalchemy as sa

revision = "g4b5c6d7e8f9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "candidates",
        sa.Column("orientation", sa.String(20), nullable=True),
    )


def downgrade():
    op.drop_column("candidates", "orientation")
