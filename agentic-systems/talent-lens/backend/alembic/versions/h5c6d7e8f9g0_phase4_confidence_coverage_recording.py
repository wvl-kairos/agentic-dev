"""Phase 4: confidence level, assessment status, recording URL

Adds:
- criterion_scores.confidence_level VARCHAR(20) DEFAULT 'demonstrated'
- criterion_scores.assessment_status VARCHAR(20) DEFAULT 'assessed_positive'
- interviews.recording_url TEXT nullable

Revision ID: h5c6d7e8f9g0
Revises: g4b5c6d7e8f9
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = "h5c6d7e8f9g0"
down_revision = "g4b5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "criterion_scores",
        sa.Column(
            "confidence_level",
            sa.String(20),
            server_default="demonstrated",
            nullable=False,
        ),
    )
    op.add_column(
        "criterion_scores",
        sa.Column(
            "assessment_status",
            sa.String(20),
            server_default="assessed_positive",
            nullable=False,
        ),
    )
    op.add_column(
        "interviews",
        sa.Column("recording_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interviews", "recording_url")
    op.drop_column("criterion_scores", "assessment_status")
    op.drop_column("criterion_scores", "confidence_level")
