"""Add in_pipeline flag to candidate_applications.

Revision ID: 010_in_pipeline
Revises: 009_pipeline_stages
Create Date: 2026-07-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_in_pipeline"
down_revision: Union[str, Sequence[str], None] = "009_pipeline_stages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidate_applications",
        sa.Column(
            "in_pipeline",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Backfill: already progressed past Applied, or has stage history → in pipeline
    op.execute(
        sa.text(
            """
            UPDATE candidate_applications ca
            SET in_pipeline = true
            WHERE EXISTS (
                SELECT 1 FROM application_stage_history h
                WHERE h.application_id = ca.id
            )
            OR EXISTS (
                SELECT 1 FROM pipeline_stages ps
                WHERE ps.id = ca.current_stage
                  AND ps.name IS DISTINCT FROM 'Applied'
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("candidate_applications", "in_pipeline")
