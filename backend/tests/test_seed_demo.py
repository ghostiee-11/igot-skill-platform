import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.demo_catalog import COURSES
from app.core.seed_demo import DEMO_EMAIL_DOMAIN, HISTORY_DAYS, QUIZ_SOURCE_TITLES, seed_demo
from app.models.models import (
    AssessmentAttempt, Course, Enrollment, GapAnalysis, QuizAttempt, Recommendation, StatEngineMastery, User,
)


@pytest.fixture(name="db")
def fixture_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_seed_demo_builds_a_complete_dataset_and_is_idempotent(db):
    summary = seed_demo(db, use_llm=False, index_vectors=False)

    assert summary["new_courses"] == len(COURSES)
    assert summary["new_officials"] == 36
    assert summary["learners_seeded"] == 36
    assert summary["quizzes"] == len(QUIZ_SOURCE_TITLES)

    course = db.query(Course).filter_by(title=COURSES[0]["title"]).one()
    assert len(course.modules) == 2 and len(course.assessment.questions) >= 4

    official = db.query(User).filter(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}")).first()
    assert db.query(GapAnalysis).filter_by(user_id=official.id).count() == 4 * (1 + len(HISTORY_DAYS))
    assert db.query(Enrollment).count() >= 36 * 3
    assert db.query(AssessmentAttempt).count() > 0
    assert db.query(StatEngineMastery).count() > 0
    assert db.query(QuizAttempt).count() > 0
    assert db.query(Recommendation).count() > 0

    counts = (db.query(Course).count(), db.query(User).count(), db.query(Enrollment).count(), db.query(GapAnalysis).count())
    again = seed_demo(db, use_llm=False, index_vectors=False)
    assert again == {"new_courses": 0, "new_officials": 0, "learners_seeded": 0, "quizzes": 0, "courses_indexed": 0}
    assert counts == (db.query(Course).count(), db.query(User).count(), db.query(Enrollment).count(), db.query(GapAnalysis).count())
