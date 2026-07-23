"""Add portal_url to clients and widen submission_format to Text."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "004_clients_add_portal_url"
down_revision = "003_attendance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Skipped when column already exists via 001 create_all with current models.
    cols = {c["name"] for c in inspect(op.get_bind()).get_columns("clients")}
    if "portal_url" not in cols:
        op.add_column("clients", sa.Column("portal_url", sa.String(500), nullable=True))
    op.alter_column(
        "clients",
        "submission_format",
        existing_type=sa.String(255),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "clients",
        "submission_format",
        existing_type=sa.Text(),
        type_=sa.String(255),
        existing_nullable=True,
    )
    op.drop_column("clients", "portal_url")
