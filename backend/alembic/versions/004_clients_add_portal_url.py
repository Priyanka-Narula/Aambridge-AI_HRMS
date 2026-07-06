"""Add portal_url to clients and widen submission_format to Text."""

import sqlalchemy as sa
from alembic import op

revision = "004_clients_add_portal_url"
down_revision = "003_attendance"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
