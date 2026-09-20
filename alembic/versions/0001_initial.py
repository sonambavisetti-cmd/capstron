"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-09-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # NOTE: This initial migration is intentionally lightweight. Models
    # are defined in dev/models.py and Alembic autogeneration can be used
    # to produce a more detailed migration when the project matures.
    pass


def downgrade():
    pass
