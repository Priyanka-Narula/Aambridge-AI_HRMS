"""Add submission metadata and owner_status to candidate_applications.

Revision ID: 007_candidate_submission
Revises: 006_job_requirement_assigned_to
Create Date: 2026-07-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "007_candidate_submission"
down_revision = "006_job_requirement_assigned_to"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_applications",
        sa.Column(
            "submitted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "candidate_applications",
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidate_applications",
        sa.Column(
            "owner_status",
            sa.String(50),
            nullable=False,
            server_default="pending_review",
        ),
    )
    op.create_foreign_key(
        "fk_candidate_applications_submitted_by_users",
        "candidate_applications",
        "users",
        ["submitted_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_candidate_applications_submitted_by_users",
        "candidate_applications",
        type_="foreignkey",
    )
    op.drop_column("candidate_applications", "owner_status")
    op.drop_column("candidate_applications", "submitted_at")
    op.drop_column("candidate_applications", "submitted_by")
