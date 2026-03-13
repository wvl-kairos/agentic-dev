"""Phase 2: salary, priority, survey_level fields

Add salary/role_type to role_templates, salary_expected to candidates,
priority to role_technology_requirements, and survey_level to
role_capability_requirements. All columns nullable or with defaults
for zero-downtime migration.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-03-13
"""

from alembic import op
import sqlalchemy as sa

revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Technology priority: must_have / should_have / nice_to_have
    op.add_column(
        "role_technology_requirements",
        sa.Column("priority", sa.String(20), server_default="must_have", nullable=False),
    )

    # Role template salary and type
    op.add_column("role_templates", sa.Column("salary_min", sa.Integer(), nullable=True))
    op.add_column("role_templates", sa.Column("salary_max", sa.Integer(), nullable=True))
    op.add_column(
        "role_templates",
        sa.Column("salary_currency", sa.String(10), server_default="USD", nullable=False),
    )
    op.add_column("role_templates", sa.Column("role_type", sa.String(100), nullable=True))

    # Candidate salary
    op.add_column("candidates", sa.Column("salary_expected", sa.Integer(), nullable=True))

    # Survey level (1-10 scale)
    op.add_column(
        "role_capability_requirements",
        sa.Column("survey_level", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("role_capability_requirements", "survey_level")
    op.drop_column("candidates", "salary_expected")
    op.drop_column("role_templates", "role_type")
    op.drop_column("role_templates", "salary_currency")
    op.drop_column("role_templates", "salary_max")
    op.drop_column("role_templates", "salary_min")
    op.drop_column("role_technology_requirements", "priority")
