"""Create competency-owned schema and tables."""
from alembic import op
from igot_competency.adapters.database import Base,SCHEMA
from igot_competency.domain import models  # noqa: F401
revision="0001_competency"; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    Base.metadata.create_all(bind=op.get_bind())
def downgrade(): Base.metadata.drop_all(bind=op.get_bind())
