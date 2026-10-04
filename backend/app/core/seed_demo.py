"""Seeds a realistic demo dataset: catalogue, officials, learning activity, competency
evidence, 30 days of gap-analysis history, recommendations and practice quizzes.

Every section is idempotent, so running the seed twice adds nothing the second time.
"""
import datetime
import json
import logging
import math
import random
from pathlib import Path
from statistics import mean
from typing import Callable, Dict, List

from sqlalchemy.orm import Session, selectinload

from app.agents.competency.gap_agent import run_gap_analysis
from app.agents.competency.target_levels import resolve_tier
from app.agents.quiz.generator import DIFFICULTIES, generate_quiz_questions
from app.agents.recommendation.agent import generate_recommendations
from app.core.demo_catalog import COURSES, DIVISIONS, EDUCATION, FIRST_NAMES, INTERESTS, RANKS, SURNAMES
from app.core.security import get_password_hash
from app.core.seed_competencies import (
    STAT_ENGINE_SKILL_TO_COMPETENCY_CODE,
    seed_competency_taxonomy,
    seed_evidence_mapping,
)
from app.models.models import (
    AssessmentAttempt,
    Assessment,
    BehaviouralSessionResult,
    Competency,
    Course,
    CourseSkill,
    Enrollment,
    GapAnalysis,
    GeneratedQuiz,
    GeneratedQuizQuestion,
    LearningHistory,
    Lesson,
    Module,
    Progress,
    Question,
    QuizAttempt,
    Skill,
    StatEngineMastery,
    User,
    UserCompetencyScore,
    UserProfile,
    UserSkill,
)

logger = logging.getLogger(__name__)

DEMO_EMAIL_DOMAIN = "igot-demo.in"
DEMO_PASSWORD = "Demo@123"
TIER_BASE_LEVEL = {"senior": 2.8, "middle": 2.2, "junior": 1.5, "default": 1.9}
CARRYFORWARD_COMPETENCIES = ["Decision Making", "Ethical Judgement", "Leadership", "Communication", "Situational Awareness", "Accountability"]
HISTORY_DAYS = (28, 23, 18, 13, 8, 3)
QUIZ_TITLE_PREFIX = "Practice quiz: "
QUIZ_SOURCE_TITLES = [
    "National Accounts Statistics & GDP Compilation",
    "Periodic Labour Force Survey (PLFS): Concepts & Estimation",
    "Data Privacy & the DPDP Act, 2023 for Statistical Offices",
    "R for Survey Data Analysis",
    "Leadership for Statistical Teams",
]
PRIOR_TRAINING = [
    "Foundation course for Indian Statistical Service probationers, NSSTA",
    "Refresher course on sampling techniques",
    "Workshop on data visualisation for official statistics",
    "Training on CAPI-based data collection",
    "Orientation on SDG monitoring frameworks",
]


ASSESSMENT_BANK_PATH = Path(__file__).with_name("assessment_bank.json")
MINUTES_PER_QUESTION = 1.25
PASS_THRESHOLD = 70.0

# One verified YouTube video per course. A plain URL goes on the course's first reading lesson;
# a (url, lesson title) pair targets that lesson. Every id was checked against YouTube oEmbed.
LESSON_VIDEOS = {
    "Fundamentals of National Sample Surveys (NSS)": "https://www.youtube.com/watch?v=_0WoqKgMnKs",
    "Compilation of Consumer Price Index (CPI) & Inflation Metrics": "https://www.youtube.com/watch?v=t2BXjbiLmMo",
    "National Accounts Statistics & GDP Compilation": "https://www.youtube.com/watch?v=WaKkU25C1-E",
    "SDG Indicators & the National Indicator Framework": "https://www.youtube.com/watch?v=M-iJM02m_Hg",
    "Index of Industrial Production (IIP) & Industrial Statistics": "https://www.youtube.com/watch?v=PRl3wUj-vLM",
    "SQL for Official Statistics Databases": "https://www.youtube.com/watch?v=HXV3zeQKqGY",
    "R for Survey Data Analysis": "https://www.youtube.com/watch?v=4xfRZp_8XFs",
    "GIS & Geospatial Analysis for Statistics": "https://www.youtube.com/watch?v=WpoSofhf9Y0",
    "Machine Learning for Official Statistics": "https://www.youtube.com/watch?v=PeMlggyqz0Y",
    "Cloud Computing & Data Engineering on Government Cloud": "https://www.youtube.com/watch?v=M988_fsOSWo",
    "Data Privacy & the DPDP Act, 2023 for Statistical Offices": "https://www.youtube.com/watch?v=8XuQFVF7ipg",
    "Digital Signatures, eSign & PKI in Government Workflows": "https://www.youtube.com/watch?v=s22eJ1eVLTU",
    "Cybersecurity Essentials for Government Data Systems": "https://www.youtube.com/watch?v=EqNe55IzjAw",
    "Communicating Statistics to Policymakers and the Public": "https://www.youtube.com/watch?v=Hfx1X9WSGYQ",
    "Project Management for Large-Scale Surveys": "https://www.youtube.com/watch?v=AOmS_UrnBD0",
    "Data Quality Frameworks & Official Statistics in India": "https://www.youtube.com/watch?v=FckTWnJl9tc",
    "Digital Governance & Public Financial Management System (PFMS)": "https://www.youtube.com/watch?v=6_ntDCR9kuE",
    "Python and Statistical Computing for Public Policy": "https://www.youtube.com/watch?v=gtjxAH8uaP0",
    "Digital Governance, Cyber Defense & Public Digital Architecture": (
        "https://www.youtube.com/watch?v=DExPHdfbf9s",
        "Lesson 2: SOC Authentication Telemetry & Incident Triage",
    ),
    "Periodic Labour Force Survey (PLFS): Concepts & Estimation": "https://www.youtube.com/watch?v=ErOa47rsDcE",
    "Agricultural Statistics & Crop Estimation Surveys": ("https://www.youtube.com/watch?v=kQGlZTXRW1U", "Crop cutting experiments"),
    "Leadership for Statistical Teams": "https://www.youtube.com/watch?v=hxgpvK8gJtg",
    "Ethics, Integrity & Professional Independence in Official Statistics": "https://www.youtube.com/watch?v=moKAMtjxGTU",
    "Change Management & Decision Making in Public Organisations": ("https://www.youtube.com/watch?v=8mVrDT9Atfc", "Creating urgency and a vision"),
}


def assessment_question_target(lesson_count: int) -> int:
    # Single-lesson courses do not carry enough material to ground a 15-question exam.
    return 15 if lesson_count >= 3 else 10


def assessment_time_limit(question_count: int) -> int:
    return max(10, math.ceil(question_count * MINUTES_PER_QUESTION / 5) * 5)


class _OfflineLLM:
    """Stands in for an LLM when seeding without network access; forces the rule-based quiz generator."""

    def invoke(self, prompt):
        raise RuntimeError("LLM disabled for offline seeding")


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _mastery_level(score: float) -> str:
    if score >= 90:
        return "master"
    if score >= 75:
        return "advanced"
    if score >= 50:
        return "intermediate"
    if score >= 25:
        return "basic"
    return "novice"


def _division_for(profile: UserProfile):
    for division in DIVISIONS:
        if profile.department == division[0]:
            return division
    role = f"{profile.job_role or ''} {profile.department or ''}".lower()
    if "price" in role or "cpi" in role:
        return DIVISIONS[4]
    if "survey" in role or "field" in role:
        return DIVISIONS[0]
    return DIVISIONS[9]


def seed_demo_catalog(db: Session, rng: random.Random) -> List[Course]:
    created = []
    skills = {s.name: s for s in db.query(Skill).all()}
    for spec in COURSES:
        if db.query(Course).filter_by(title=spec["title"]).first():
            continue
        enrolled = rng.randint(260, 3400)
        course = Course(
            title=spec["title"],
            overview=spec["overview"],
            instructor=spec["instructor"],
            organization=spec["organization"],
            duration_hours=spec["hours"],
            difficulty=spec["difficulty"],
            source="internal",
            category=spec["category"],
            rating=round(rng.uniform(4.45, 4.95), 2),
            enrolled_count=enrolled,
            is_popular=enrolled > 2200,
            is_new=rng.random() < 0.35,
        )
        db.add(course)
        db.flush()

        for name, category in spec["skills"]:
            if name not in skills:
                skills[name] = Skill(name=name, category=category)
                db.add(skills[name])
                db.flush()
            db.add(CourseSkill(course_id=course.id, skill_id=skills[name].id))

        lesson_specs = []
        for module_order, module_spec in enumerate(spec["modules"], start=1):
            module = Module(course_id=course.id, title=module_spec["title"], description=module_spec["description"], order=module_order)
            db.add(module)
            db.flush()
            for lesson_order, lesson_spec in enumerate(module_spec["lessons"], start=1):
                db.add(Lesson(
                    module_id=module.id,
                    title=lesson_spec["title"],
                    content_type="reading",
                    duration_minutes=lesson_spec["minutes"],
                    content=f"# {lesson_spec['title']}\n\n" + "\n".join(f"- {p}" for p in lesson_spec["points"]),
                    activity_question=lesson_spec["question"],
                    activity_options_json=json.dumps(lesson_spec["options"]),
                    activity_correct_option=lesson_spec["answer"],
                    activity_explanation=lesson_spec["explanation"],
                    order=lesson_order,
                ))
                lesson_specs.append(lesson_spec)

        assessment = Assessment(
            course_id=course.id,
            title=f"{spec['title']}: Final Assessment",
            description="Answer every question. A score of 70% is required to pass and earn the course certificate.",
            time_limit_minutes=15,
            pass_threshold_percent=70.0,
        )
        db.add(assessment)
        db.flush()
        for order, lesson_spec in enumerate(lesson_specs, start=1):
            db.add(Question(
                assessment_id=assessment.id,
                text=lesson_spec["question"],
                options_json=json.dumps(lesson_spec["options"]),
                correct_option_index=lesson_spec["answer"],
                explanation=lesson_spec["explanation"],
                order=order,
            ))
        created.append(course)
    db.commit()
    return created


def seed_demo_officials(db: Session, rng: random.Random) -> List[User]:
    if db.query(User).filter(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}")).first():
        return []
    password_hash = get_password_hash(DEMO_PASSWORD)
    designations = [(designation, years) for designation, count, years in RANKS for _ in range(count)]
    users = []
    for i, (designation, years) in enumerate(designations):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = SURNAMES[(i * 7) % len(SURNAMES)]
        division_name, job_role, _ = DIVISIONS[i % len(DIVISIONS)]
        user = User(
            email=f"{first}.{last}@{DEMO_EMAIL_DOMAIN}".lower(),
            password_hash=password_hash,
            full_name=f"{first} {last}",
            role="learner",
            created_at=_now() - datetime.timedelta(days=rng.randint(120, 400)),
        )
        db.add(user)
        db.flush()
        db.add(UserProfile(
            user_id=user.id,
            designation=designation,
            department=division_name,
            job_role=job_role,
            education=rng.choice(EDUCATION),
            work_experience_years=max(1, years + rng.randint(-2, 3)),
            prior_training=rng.choice(PRIOR_TRAINING),
            current_assignment=job_role,
            areas_of_interest=rng.choice(INTERESTS),
            onboarding_completed=True,
            daily_goal_minutes=rng.choice([20, 30, 45, 60]),
            current_streak_days=rng.randint(0, 24),
            last_active_date=_now() - datetime.timedelta(days=rng.randint(0, 6)),
        ))
        users.append(user)
    db.commit()
    return users


def seed_competency_evidence(
    db: Session, user: User, profile: UserProfile, rng: random.Random, competencies_by_domain: Dict[str, List[Competency]]
) -> bool:
    """Returns False when the user already has competency evidence (nothing seeded)."""
    if db.query(UserCompetencyScore).filter_by(user_id=user.id).first():
        return False
    base = TIER_BASE_LEVEL[resolve_tier(profile.designation, profile.job_role)]
    affinity = _division_for(profile)[2]

    domain_levels = {}
    for code, competencies in competencies_by_domain.items():
        domain_level = base + affinity.get(code, 0.0) + rng.gauss(0, 0.35)
        domain_levels[code] = domain_level
        for competency in rng.sample(competencies, k=min(len(competencies), rng.randint(2, 4))):
            db.add(UserCompetencyScore(
                user_id=user.id,
                competency_id=competency.id,
                level=round(_clamp(domain_level + rng.gauss(0, 0.5), 0.4, 4.9), 2),
                evidence_source=rng.choice(["self_declared", "assessment", "assessment"]),
            ))

    if affinity.get("statistical", 0.0) >= 0.6:
        for skill_id in rng.sample(list(STAT_ENGINE_SKILL_TO_COMPETENCY_CODE), k=rng.randint(2, 4)):
            score = round(_clamp((domain_levels["statistical"] + rng.gauss(0, 0.4)) * 20, 12, 97), 1)
            attempts = rng.randint(6, 40)
            db.add(StatEngineMastery(
                user_id=str(user.id),
                skill_id=skill_id,
                mastery_json=json.dumps({
                    "skill_id": skill_id,
                    "score": score,
                    "level": _mastery_level(score),
                    "confidence": round(_clamp(score / 100 + 0.1, 0.1, 1.0), 2),
                    "attempts_count": attempts,
                    "correct_count": round(attempts * score / 100),
                    "remediation_recommended": score < 40,
                    "last_attempt_at": (_now() - datetime.timedelta(days=rng.randint(0, 20))).isoformat(),
                }),
            ))

    if rng.random() < 0.6:
        scores = {
            name: round(_clamp((domain_levels["behavioural"] + rng.gauss(0, 0.4)) * 20, 45, 96), 1)
            for name in CARRYFORWARD_COMPETENCIES
        }
        overall = round(mean(scores.values()), 1)
        db.add(BehaviouralSessionResult(
            session_id=f"demo-cf-{user.id}",
            session_type="carryforward",
            user_id=user.id,
            case_or_course_id="case_mospi_nqaf_audit",
            score=overall,
            result_json=json.dumps({"procedural_compliance_score": overall, "competency_scores": scores}),
            completed_at=_now() - datetime.timedelta(days=rng.randint(1, 25)),
        ))
    db.commit()
    return True


def seed_learning_activity(db: Session, user: User, courses: List[Course], rng: random.Random) -> None:
    if db.query(Enrollment).filter_by(user_id=user.id).first():
        return
    now = _now()
    earned_skills = set()
    for course in rng.sample(courses, k=min(len(courses), rng.randint(3, 6))):
        lessons = [lesson for module in course.modules for lesson in module.lessons]
        if not lessons:
            continue
        started = now - datetime.timedelta(days=rng.randint(12, 150), hours=rng.randint(0, 20))
        completed = rng.random() < 0.4
        if completed:
            progress = 100.0
            done = lessons
            completed_at = min(now - datetime.timedelta(days=1), started + datetime.timedelta(days=rng.randint(4, 35)))
        else:
            progress = float(rng.randint(8, 85))
            done = lessons[: max(1, round(len(lessons) * progress / 100))]
            completed_at = None

        enrollment = Enrollment(
            user_id=user.id,
            course_id=course.id,
            status="completed" if completed else "in_progress",
            started_at=started,
            completed_at=completed_at,
            progress_percent=progress,
            last_lesson_id=done[-1].id,
        )
        db.add(enrollment)
        db.flush()
        for step, lesson in enumerate(done):
            db.add(Progress(
                enrollment_id=enrollment.id,
                module_id=lesson.module_id,
                lesson_id=lesson.id,
                completed=True,
                activity_completed=rng.random() < 0.85,
                updated_at=started + datetime.timedelta(days=step),
            ))
        db.add(LearningHistory(user_id=user.id, course_id=course.id, viewed_at=started))

        assessment = course.assessment
        if completed and assessment and assessment.questions:
            accuracy = rng.uniform(0.55, 1.0)
            answers, correct = {}, 0
            for question in assessment.questions:
                option_count = len(json.loads(question.options_json)) or 4
                if rng.random() < accuracy:
                    answers[str(question.id)] = question.correct_option_index
                    correct += 1
                else:
                    answers[str(question.id)] = (question.correct_option_index + 1) % option_count
            score = round(100.0 * correct / len(assessment.questions), 1)
            db.add(AssessmentAttempt(
                user_id=user.id,
                assessment_id=assessment.id,
                score_percent=score,
                passed=score >= assessment.pass_threshold_percent,
                answers_json=json.dumps(answers),
                submitted_at=completed_at,
            ))

        if completed:
            for course_skill in course.course_skills:
                if course_skill.skill_id not in earned_skills:
                    earned_skills.add(course_skill.skill_id)
                    db.add(UserSkill(user_id=user.id, skill_id=course_skill.skill_id, source_course_id=course.id, acquired_at=completed_at))
    db.commit()


def seed_gap_history(db: Session, user: User, rng: random.Random) -> None:
    """Runs a real gap analysis for today, then backfills earlier snapshots that close towards it."""
    result = run_gap_analysis(db, user.id)
    now = _now()
    for gap in result["gaps"]:
        improvement = rng.uniform(0.25, 1.1)
        for days in HISTORY_DAYS:
            past_gap = min(gap.target_level, gap.gap + improvement * days / HISTORY_DAYS[0])
            db.add(GapAnalysis(
                user_id=user.id,
                domain_id=gap.domain_id,
                target_level=gap.target_level,
                current_level=round(max(0.0, gap.target_level - past_gap), 2),
                gap=round(past_gap, 2),
                generated_at=now - datetime.timedelta(days=days, hours=rng.randint(0, 9)),
            ))
    db.commit()


def seed_demo_quizzes(db: Session, learners: List[User], use_llm: bool, rng: random.Random) -> List[GeneratedQuiz]:
    if db.query(GeneratedQuiz).filter(GeneratedQuiz.title.like(f"{QUIZ_TITLE_PREFIX}%")).first() or not learners:
        return []
    trainer = next(
        (u for u in learners if u.profile and "Director" in (u.profile.designation or "") and "NSSTA" in (u.profile.department or "")),
        learners[0],
    )
    llm_client = None if use_llm else _OfflineLLM()
    created = []
    for title in QUIZ_SOURCE_TITLES:
        course = db.query(Course).filter_by(title=title).first()
        if not course:
            continue
        text = "\n\n".join(lesson.content for module in course.modules for lesson in module.lessons)
        difficulty = course.difficulty if course.difficulty in DIFFICULTIES else "intermediate"
        try:
            questions, generator = generate_quiz_questions(text, 6, difficulty, llm_client=llm_client)
        except Exception as e:
            logger.warning("Skipping demo quiz for %s: %s", title, e)
            continue
        if not questions:
            continue

        quiz = GeneratedQuiz(
            user_id=trainer.id,
            title=f"{QUIZ_TITLE_PREFIX}{course.title}",
            source_name=f"{course.title} (course notes)",
            source_type="course",
            source_excerpt=text[:1000],
            difficulty=difficulty,
            generator=generator,
            created_at=_now() - datetime.timedelta(days=rng.randint(10, 28)),
        )
        db.add(quiz)
        db.flush()
        stored = []
        for order, q in enumerate(questions, start=1):
            question = GeneratedQuizQuestion(
                quiz_id=quiz.id, order=order, question_text=q["question"], options_json=json.dumps(q["options"]),
                correct_option_index=q["correct_index"], explanation=q["explanation"], concept=q["concept"],
            )
            db.add(question)
            stored.append(question)
        db.flush()

        for learner in rng.sample(learners, k=min(len(learners), rng.randint(8, 18))):
            accuracy = rng.uniform(0.45, 0.95)
            answers, correct = {}, 0
            for question in stored:
                if rng.random() < accuracy:
                    answers[str(question.id)] = question.correct_option_index
                    correct += 1
                else:
                    answers[str(question.id)] = (question.correct_option_index + 1) % 4
            db.add(QuizAttempt(
                quiz_id=quiz.id,
                user_id=learner.id,
                answers_json=json.dumps(answers),
                correct_count=correct,
                total_questions=len(stored),
                score_percent=round(100.0 * correct / len(stored), 1),
                submitted_at=quiz.created_at + datetime.timedelta(days=rng.randint(1, 9)),
            ))
        created.append(quiz)
    db.commit()
    return created


def apply_assessment_bank(db: Session) -> int:
    """Loads the generated final-assessment bank so exams no longer repeat the lesson practice questions.

    Idempotent: an assessment is rebuilt only when its question texts differ from the bank.
    Time limits are recomputed for every assessment from its question count.
    """
    bank = json.loads(ASSESSMENT_BANK_PATH.read_text(encoding="utf-8")) if ASSESSMENT_BANK_PATH.exists() else {}
    rebuilt = 0
    courses = db.query(Course).options(selectinload(Course.assessment).selectinload(Assessment.questions)).all()
    for course in courses:
        items = bank.get(course.title)
        assessment = course.assessment
        if not items:
            if assessment and assessment.questions:
                assessment.time_limit_minutes = assessment_time_limit(len(assessment.questions))
            continue
        if assessment is None:
            assessment = Assessment(
                course_id=course.id,
                title=f"{course.title}: Final Assessment",
                description="Answer every question. A score of 70% is required to pass and earn the course certificate.",
                pass_threshold_percent=PASS_THRESHOLD,
            )
            db.add(assessment)
            db.flush()
        if [q.text for q in assessment.questions] != [item["question"] for item in items]:
            assessment.questions.clear()
            db.flush()
            for order, item in enumerate(items, start=1):
                assessment.questions.append(Question(
                    text=item["question"],
                    options_json=json.dumps(item["options"]),
                    correct_option_index=item["correct_index"],
                    explanation=item["explanation"],
                    order=order,
                ))
            rebuilt += 1
        assessment.time_limit_minutes = assessment_time_limit(len(items))
    db.commit()
    return rebuilt


def attach_lesson_videos(db: Session) -> int:
    attached = 0
    for title, entry in LESSON_VIDEOS.items():
        url, lesson_title = (entry, None) if isinstance(entry, str) else entry
        course = db.query(Course).filter_by(title=title).first()
        if not course:
            continue
        lessons = [l for m in course.modules for l in m.lessons]
        target = (
            next((l for l in lessons if l.title == lesson_title), None)
            or next((l for l in lessons if l.content_type == "video"), None)
            or next((l for l in lessons if l.content_type == "reading"), None)
            or next(iter(lessons), None)
        )
        if target and target.video_url != url:
            # Labs keep their type and show the video above the lab launcher.
            if target.content_type == "reading":
                target.content_type = "video"
            target.video_url = url
            attached += 1
    db.commit()
    return attached


def seed_demo(
    db: Session, use_llm: bool = True, index_vectors: bool = True, log: Callable[[str], None] = logger.info
) -> dict:
    rng = random.Random(2026)
    seed_competency_taxonomy(db)
    seed_evidence_mapping(db)

    new_courses = seed_demo_catalog(db, rng)
    log(f"Catalogue: {len(new_courses)} new courses")
    new_officials = seed_demo_officials(db, rng)
    log(f"Officials: {len(new_officials)} new demo officials")
    log(f"Assessments: {apply_assessment_bank(db)} rebuilt from the question bank")
    log(f"Videos: {attach_lesson_videos(db)} lessons linked to a video")

    competencies_by_domain: Dict[str, List[Competency]] = {}
    for competency in db.query(Competency).all():
        competencies_by_domain.setdefault(competency.domain.code, []).append(competency)
    courses = db.query(Course).all()
    learners = db.query(User).filter(User.role != "admin").all()

    seeded = 0
    for index, user in enumerate(learners, start=1):
        if not user.profile or not seed_competency_evidence(db, user, user.profile, rng, competencies_by_domain):
            continue
        seed_learning_activity(db, user, courses, rng)
        seed_gap_history(db, user, rng)
        generate_recommendations(db, user.id)
        seeded += 1
        log(f"  [{index}/{len(learners)}] {user.full_name}")

    quizzes = seed_demo_quizzes(db, learners, use_llm, rng)
    log(f"Quizzes: {len(quizzes)} practice quizzes")

    indexed = 0
    if index_vectors and new_courses:
        from app.agents.recommendation.indexer import index_course
        for course in new_courses:
            try:
                index_course(db, course.id)
                indexed += 1
            except Exception as e:
                logger.warning("Could not index course %s in Pinecone: %s", course.id, e)
        log(f"Pinecone: indexed {indexed} courses")

    return {
        "new_courses": len(new_courses),
        "new_officials": len(new_officials),
        "learners_seeded": seeded,
        "quizzes": len(quizzes),
        "courses_indexed": indexed,
    }
