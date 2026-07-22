"""add uae_experience_years and industry to candidates

Revision ID: 004_candidate_uae_industry
Revises: 003_attendance
Create Date: 2026-07-03 13:27:43.701328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "004_candidate_uae_industry"
down_revision: Union[str, Sequence[str], None] = '003_attendance'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Skipped when columns already exist via 001 create_all with current models.
    cols = {c["name"] for c in inspect(op.get_bind()).get_columns("candidates")}
    if "uae_experience_years" not in cols:
        op.add_column(
            "candidates",
            sa.Column("uae_experience_years", sa.Numeric(4, 2), nullable=True),
        )
    if "industry" not in cols:
        op.add_column(
            "candidates",
            sa.Column("industry", sa.String(length=100), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("candidates", "industry")
    op.drop_column("candidates", "uae_experience_years")
