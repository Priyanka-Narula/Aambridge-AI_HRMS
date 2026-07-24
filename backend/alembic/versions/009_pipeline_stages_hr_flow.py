"""Upgrade pipeline stages for HR shortlist-to-joining flow.

Revision ID: 009_pipeline_stages
Revises: 008_submission_data
Create Date: 2026-07-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_pipeline_stages"
down_revision: Union[str, Sequence[str], None] = "008_submission_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Target stages for staffing pipeline after client shortlist feedback.
TARGET_STAGES = [
    ("Applied", 1),
    ("Shortlisted", 2),
    ("Screening", 3),
    ("Interview", 4),
    ("Offer", 5),
    ("Joined", 6),
    ("On Hold", 7),
    ("Rejected", 8),
]


def upgrade() -> None:
    conn = op.get_bind()

    # Rename legacy "Placed" → "Joined" if present
    conn.execute(
        sa.text(
            "UPDATE pipeline_stages SET name = 'Joined' "
            "WHERE name = 'Placed' AND NOT EXISTS ("
            "  SELECT 1 FROM pipeline_stages WHERE name = 'Joined'"
            ")"
        )
    )

    existing = {
        row[0]: row[1]
        for row in conn.execute(sa.text("SELECT name, id FROM pipeline_stages")).fetchall()
    }

    for name, order_no in TARGET_STAGES:
        if name in existing:
            conn.execute(
                sa.text(
                    "UPDATE pipeline_stages SET order_no = :order_no WHERE name = :name"
                ),
                {"order_no": order_no, "name": name},
            )
        else:
            conn.execute(
                sa.text(
                    "INSERT INTO pipeline_stages (id, name, order_no) "
                    "VALUES (gen_random_uuid(), :name, :order_no)"
                ),
                {"name": name, "order_no": order_no},
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE pipeline_stages SET name = 'Placed' "
            "WHERE name = 'Joined' AND NOT EXISTS ("
            "  SELECT 1 FROM pipeline_stages WHERE name = 'Placed'"
            ")"
        )
    )
    # Leave Shortlisted / On Hold in place — safe no-op for downgrade of additive stages.
    conn.execute(
        sa.text(
            "UPDATE pipeline_stages SET order_no = CASE name "
            "WHEN 'Applied' THEN 1 "
            "WHEN 'Screening' THEN 2 "
            "WHEN 'Interview' THEN 3 "
            "WHEN 'Offer' THEN 4 "
            "WHEN 'Placed' THEN 5 "
            "WHEN 'Joined' THEN 5 "
            "WHEN 'Rejected' THEN 6 "
            "ELSE order_no END"
        )
    )
