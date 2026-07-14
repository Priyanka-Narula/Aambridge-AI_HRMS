"""Add submission_data JSON column to candidate_applications.

Revision ID: 008_submission_data
Revises: 007_candidate_submission
Create Date: 2026-07-14
"""

import sqlalchemy as sa
from alembic import op

revision = "008_submission_data"
down_revision = "007_candidate_submission"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_applications",
        sa.Column("submission_data", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidate_applications", "submission_data")
