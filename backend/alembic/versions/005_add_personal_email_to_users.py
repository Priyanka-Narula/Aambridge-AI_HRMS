"""Add personal_email to users.

Revision ID: 005_add_personal_email_to_users
Revises: c1d649d65fa9
Create Date: 2026-07-08
"""

import sqlalchemy as sa
from alembic import op

revision = "005_add_personal_email_to_users"
down_revision = "c1d649d65fa9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("personal_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "personal_email")

