"""Create assessment-owned baseline tables."""

from alembic import op

from igot_assessment.database import Base, SCHEMA
from igot_assessment import database  # noqa: F401

BASELINE_TABLES = tuple(
    table for name, table in Base.metadata.tables.items()
    if name not in {
        "assessment.stat_engine_attempts",
        "assessment.stat_engine_mastery",
        "assessment.generated_behavioural_cases",
    }
)

revision = "0001_assessment"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), tables=BASELINE_TABLES)


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind(), tables=BASELINE_TABLES)
