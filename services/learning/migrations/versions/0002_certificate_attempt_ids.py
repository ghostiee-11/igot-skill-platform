"""Preserve UUID attempt references issued by the assessment service."""
from alembic import op
from sqlalchemy import Integer, String

revision = "0002_certificate_attempt_ids"
down_revision = "0001_learning"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("certificates", "attempt_id", schema="learning",
                    existing_type=Integer(), type_=String(36), postgresql_using="attempt_id::text")


def downgrade():
    raise RuntimeError("UUID attempt references cannot be safely converted to legacy integers")
