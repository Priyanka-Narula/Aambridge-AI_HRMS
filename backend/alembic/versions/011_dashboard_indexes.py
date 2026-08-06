"""Add analytics dashboard query indexes.

Revision ID: 011_dashboard_indexes
Revises: 010_in_pipeline
Create Date: 2026-07-27
"""

from typing import Sequence, Union

from alembic import op

revision: str = "011_dashboard_indexes"
down_revision: Union[str, Sequence[str], None] = "010_in_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_candidates_candidate_status", "candidates", ["candidate_status"])
    op.create_index("ix_candidates_created_by", "candidates", ["created_by"])
    op.create_index(
        "ix_candidate_applications_submitted_at",
        "candidate_applications",
        ["submitted_at"],
    )
    op.create_index(
        "ix_candidate_applications_owner_status",
        "candidate_applications",
        ["owner_status"],
    )
    op.create_index(
        "ix_candidate_applications_in_pipeline",
        "candidate_applications",
        ["in_pipeline"],
    )
    op.create_index("ix_interviews_scheduled_datetime", "interviews", ["scheduled_datetime"])
    op.create_index("ix_interviews_status", "interviews", ["status"])
    op.create_index("ix_placements_joined_date", "placements", ["joined_date"])


def downgrade() -> None:
    op.drop_index("ix_placements_joined_date", table_name="placements")
    op.drop_index("ix_interviews_status", table_name="interviews")
    op.drop_index("ix_interviews_scheduled_datetime", table_name="interviews")
    op.drop_index("ix_candidate_applications_in_pipeline", table_name="candidate_applications")
    op.drop_index("ix_candidate_applications_owner_status", table_name="candidate_applications")
    op.drop_index("ix_candidate_applications_submitted_at", table_name="candidate_applications")
    op.drop_index("ix_candidates_created_by", table_name="candidates")
    op.drop_index("ix_candidates_candidate_status", table_name="candidates")
