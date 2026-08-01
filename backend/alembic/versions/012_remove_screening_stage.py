"""Remove Screening from the active hiring path.

Revision ID: 012_remove_screening
Revises: 010_in_pipeline
Create Date: 2026-07-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_remove_screening"
down_revision: Union[str, Sequence[str], None] = "010_in_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Preserve Screening history, but return active cards to the preceding stage.
    conn.execute(
        sa.text(
            """
            UPDATE candidate_applications
            SET current_stage = (
                SELECT id FROM pipeline_stages WHERE name = 'Shortlisted'
            )
            WHERE current_stage = (
                SELECT id FROM pipeline_stages WHERE name = 'Screening'
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE pipeline_stages
            SET order_no = CASE name
                WHEN 'Applied' THEN 1
                WHEN 'Shortlisted' THEN 2
                WHEN 'Interview' THEN 3
                WHEN 'Offer' THEN 4
                WHEN 'Joined' THEN 5
                WHEN 'On Hold' THEN 6
                WHEN 'Rejected' THEN 7
                WHEN 'Screening' THEN 99
                ELSE order_no
            END
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE pipeline_stages
            SET order_no = CASE name
                WHEN 'Applied' THEN 1
                WHEN 'Shortlisted' THEN 2
                WHEN 'Screening' THEN 3
                WHEN 'Interview' THEN 4
                WHEN 'Offer' THEN 5
                WHEN 'Joined' THEN 6
                WHEN 'On Hold' THEN 7
                WHEN 'Rejected' THEN 8
                ELSE order_no
            END
            """
        )
    )
