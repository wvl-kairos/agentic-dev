"""Phase 5: feedback round — recruiter_name, role status, shared links, surveys

Adds:
- candidates.recruiter_name VARCHAR(200) nullable
- role_templates.status VARCHAR(20) DEFAULT 'open'
- shared_links table
- survey_responses table
- survey_answers table

Revision ID: i6d7e8f9g0h1
Revises: h5c6d7e8f9g0
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "i6d7e8f9g0h1"
down_revision = "h5c6d7e8f9g0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # candidates.recruiter_name
    op.add_column(
        "candidates",
        sa.Column("recruiter_name", sa.String(200), nullable=True),
    )

    # role_templates.status
    op.add_column(
        "role_templates",
        sa.Column(
            "status",
            sa.String(20),
            server_default="open",
            nullable=False,
        ),
    )

    # shared_links table
    op.create_table(
        "shared_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("token", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("created_by", sa.String(200), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # survey_responses table
    op.create_table(
        "survey_responses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "role_template_id",
            UUID(as_uuid=True),
            sa.ForeignKey("role_templates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("respondent_name", sa.String(200), nullable=False),
        sa.Column("respondent_email", sa.String(320), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # survey_answers table
    op.create_table(
        "survey_answers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "survey_response_id",
            UUID(as_uuid=True),
            sa.ForeignKey("survey_responses.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "capability_id",
            UUID(as_uuid=True),
            sa.ForeignKey("capabilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("survey_answers")
    op.drop_table("survey_responses")
    op.drop_table("shared_links")
    op.drop_column("role_templates", "status")
    op.drop_column("candidates", "recruiter_name")
