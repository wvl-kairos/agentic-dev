"""add_soft_skills_cultural_fit

Revision ID: c7a3f1d8e902
Revises: eb65518f4fe1
Create Date: 2026-03-05 19:50:00.000000
"""
from typing import Sequence, Union

import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a3f1d8e902'
down_revision: Union[str, None] = 'eb65518f4fe1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reuse sa.table references for bulk_insert into existing tables
    capabilities_table = sa.table(
        'capabilities',
        sa.column('id', sa.UUID),
        sa.column('name', sa.String),
        sa.column('slug', sa.String),
        sa.column('description', sa.Text),
        sa.column('icon', sa.String),
        sa.column('order', sa.Integer),
    )
    levels_table = sa.table(
        'capability_levels',
        sa.column('id', sa.UUID),
        sa.column('capability_id', sa.UUID),
        sa.column('level', sa.Integer),
        sa.column('title', sa.String),
        sa.column('description', sa.Text),
    )
    tech_table = sa.table(
        'technologies',
        sa.column('id', sa.UUID),
        sa.column('capability_id', sa.UUID),
        sa.column('name', sa.String),
        sa.column('slug', sa.String),
        sa.column('icon', sa.String),
        sa.column('order', sa.Integer),
    )

    # --- Capability UUIDs (continuing existing pattern) ---
    CAP_SOFT_SKILLS = uuid.UUID("a0000001-0000-0000-0000-000000000008")
    CAP_CULTURAL_FIT = uuid.UUID("a0000001-0000-0000-0000-000000000009")

    CAPS = [
        {
            "id": CAP_SOFT_SKILLS,
            "name": "Soft Skills",
            "slug": "soft-skills",
            "description": "Communication, emotional intelligence, collaboration, and interpersonal effectiveness.",
            "icon": "heart-handshake",
            "order": 8,
            "levels": [
                (1, "Developing", "Shows awareness of interpersonal dynamics. Communicates clearly in structured settings with guidance."),
                (2, "Competent", "Communicates effectively in most situations. Handles basic conflicts and collaborates within team boundaries."),
                (3, "Proficient", "Demonstrates strong communication, empathy, and collaboration across teams. Navigates conflict constructively."),
                (4, "Advanced", "Influences through communication. Mentors others in soft skills. Facilitates cross-functional collaboration."),
                (5, "Expert", "Exceptional interpersonal leadership. Shapes team culture through communication. Resolves complex organizational dynamics."),
            ],
        },
        {
            "id": CAP_CULTURAL_FIT,
            "name": "Cultural Fit",
            "slug": "cultural-fit",
            "description": "Alignment with company values, adaptability, ownership mindset, and collaborative culture.",
            "icon": "globe",
            "order": 9,
            "levels": [
                (1, "Exploring", "Shows curiosity about company culture. Open to learning organizational values and norms."),
                (2, "Aligning", "Demonstrates understanding of core values. Adapts behavior to team norms. Receptive to feedback."),
                (3, "Integrated", "Embodies company values in daily work. Actively contributes to positive team culture and inclusion."),
                (4, "Champion", "Advocates for cultural values across teams. Drives initiatives around inclusion, feedback, and growth mindset."),
                (5, "Ambassador", "Defines and evolves organizational culture. Represents company values externally. Inspires cultural excellence."),
            ],
        },
    ]

    # Seed capabilities and levels
    for cap in CAPS:
        cap_id = cap["id"]
        op.bulk_insert(capabilities_table, [{
            "id": cap_id,
            "name": cap["name"],
            "slug": cap["slug"],
            "description": cap["description"],
            "icon": cap["icon"],
            "order": cap["order"],
        }])
        level_rows = []
        for level, title, desc in cap["levels"]:
            level_rows.append({
                "id": uuid.uuid4(),
                "capability_id": cap_id,
                "level": level,
                "title": title,
                "description": desc,
            })
        op.bulk_insert(levels_table, level_rows)

    # --- Seed technologies (sub-skills) for each new capability ---
    TECHS = {
        CAP_SOFT_SKILLS: [
            ("Communication", "communication"),
            ("Active Listening", "active-listening"),
            ("Conflict Resolution", "conflict-resolution"),
            ("Emotional Intelligence", "emotional-intelligence"),
            ("Presentation Skills", "presentation-skills"),
            ("Negotiation", "negotiation"),
            ("Time Management", "time-management"),
            ("Critical Thinking", "critical-thinking"),
            ("Mentoring & Coaching", "mentoring-coaching"),
            ("Teamwork", "teamwork"),
        ],
        CAP_CULTURAL_FIT: [
            ("Team Collaboration", "team-collaboration"),
            ("Diversity & Inclusion", "diversity-inclusion"),
            ("Adaptability", "adaptability"),
            ("Growth Mindset", "growth-mindset"),
            ("Ownership & Accountability", "ownership-accountability"),
            ("Feedback Culture", "feedback-culture"),
            ("Remote/Async Communication", "remote-async-communication"),
            ("Company Values Alignment", "company-values-alignment"),
            ("Work-Life Balance", "work-life-balance"),
            ("Cross-Cultural Awareness", "cross-cultural-awareness"),
        ],
    }

    tech_rows = []
    for cap_id, techs in TECHS.items():
        for idx, (name, slug) in enumerate(techs):
            tech_rows.append({
                "id": uuid.uuid4(),
                "capability_id": cap_id,
                "name": name,
                "slug": slug,
                "icon": None,
                "order": idx + 1,
            })

    op.bulk_insert(tech_table, tech_rows)


def downgrade() -> None:
    # Delete seeded data in reverse order (technologies first, then levels, then capabilities)
    op.execute(
        "DELETE FROM technologies WHERE capability_id IN ("
        "'a0000001-0000-0000-0000-000000000008',"
        "'a0000001-0000-0000-0000-000000000009'"
        ")"
    )
    op.execute(
        "DELETE FROM capability_levels WHERE capability_id IN ("
        "'a0000001-0000-0000-0000-000000000008',"
        "'a0000001-0000-0000-0000-000000000009'"
        ")"
    )
    op.execute(
        "DELETE FROM capabilities WHERE id IN ("
        "'a0000001-0000-0000-0000-000000000008',"
        "'a0000001-0000-0000-0000-000000000009'"
        ")"
    )
