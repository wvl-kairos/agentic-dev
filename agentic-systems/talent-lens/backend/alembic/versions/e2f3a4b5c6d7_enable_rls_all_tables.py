"""enable_rls_all_tables

Enable Row Level Security on all public tables to prevent unauthorized
direct access via Supabase's PostgREST API (anon key).

The FastAPI backend connects as the postgres superuser, which bypasses RLS.
A permissive policy is added for the service_role to allow Supabase dashboard
and server-side SDK access.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-11 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All application tables (excluding alembic_version which needs no protection)
TABLES = [
    "ventures",
    "candidates",
    "rubrics",
    "rubric_criteria",
    "interviews",
    "assessments",
    "criterion_scores",
    "evidence",
    "capabilities",
    "capability_levels",
    "role_templates",
    "role_capability_requirements",
    "technologies",
    "role_technology_requirements",
]


def upgrade() -> None:
    for table in TABLES:
        # Enable RLS — blocks all access unless a policy grants it
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

        # Allow service_role full access (used by Supabase dashboard & server SDK)
        op.execute(
            f"CREATE POLICY service_role_all ON {table} "
            f"FOR ALL TO service_role USING (true) WITH CHECK (true)"
        )

        # Allow postgres role full access (used by our FastAPI backend).
        # postgres is a superuser and bypasses RLS by default, but this
        # makes it explicit and covers edge cases.
        op.execute(
            f"CREATE POLICY postgres_all ON {table} "
            f"FOR ALL TO postgres USING (true) WITH CHECK (true)"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP POLICY IF EXISTS service_role_all ON {table}")
        op.execute(f"DROP POLICY IF EXISTS postgres_all ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
