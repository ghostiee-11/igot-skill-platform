"""Persist adaptive attempts, mastery, and generated behavioural cases."""

from alembic import op
from igot_assessment.database import Base

revision = "0002_adaptive_cases"
down_revision = "0001_assessment"
branch_labels = None
depends_on = None

TABLES = ("stat_engine_attempts", "stat_engine_mastery", "generated_behavioural_cases")


def upgrade():
    for name in TABLES:
        Base.metadata.tables[f"assessment.{name}"].create(op.get_bind(), checkfirst=True)


def downgrade():
    for name in reversed(TABLES):
        Base.metadata.tables[f"assessment.{name}"].drop(op.get_bind(), checkfirst=True)
