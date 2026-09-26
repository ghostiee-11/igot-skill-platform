"""Create content-owned baseline tables."""

from alembic import op

from igot_content.database import Base, SCHEMA
from igot_content import database  # noqa: F401

revision = "0001_content"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
