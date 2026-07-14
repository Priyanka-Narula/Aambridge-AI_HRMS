"""merge candidate and client migrations

Revision ID: c1d649d65fa9
Revises: 004_candidate_uae_industry, 004_clients_add_portal_url
Create Date: 2026-07-06 20:10:19.575028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d649d65fa9'
down_revision: Union[str, Sequence[str], None] = ('004_candidate_uae_industry', '004_clients_add_portal_url')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
