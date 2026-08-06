"""Seed default roles and pipeline stages."""

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "002_seed_defaults"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None

DEFAULT_ROLES = ["admin", "recruiter", "manager", "client"]
DEFAULT_PIPELINE_STAGES = [
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
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
    )
    stages_table = sa.table(
        "pipeline_stages",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("order_no", sa.Integer),
    )

    op.bulk_insert(
        roles_table,
        [{"id": uuid4(), "name": name} for name in DEFAULT_ROLES],
    )
    op.bulk_insert(
        stages_table,
        [
            {"id": uuid4(), "name": name, "order_no": order_no}
            for name, order_no in DEFAULT_PIPELINE_STAGES
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM pipeline_stages WHERE name IN "
            "('Applied', 'Shortlisted', 'Screening', 'Interview', 'Offer', "
            "'Joined', 'Placed', 'On Hold', 'Rejected')"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM roles WHERE name IN ('admin', 'recruiter', 'manager', 'client')"
        )
    )
