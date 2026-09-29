import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_, and_
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import (
    User, Course, Module, Enrollment, Progress, PlannedCourse,
    LearningHistory, UserSkill, Lesson, Recommendation, AssessmentAttempt
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

RECOMMENDED_COURSE_COUNT = 4


@router.get("/summary")
def get_dashboard_summary(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If unauthenticated, return public preview highlights
    if not current_user:
        popular_courses = db.query(Course).order_by(Course.enrolled_count.desc()).limit(4).all()
        return {
            "authenticated": False,
            "recommended": [
                {
                    "id": c.id,
                    "title": c.title,
                    "overview": c.overview,
                    "instructor": c.instructor,
                    "organization": c.organization,
                    "duration_hours": c.duration_hours,
                    "difficulty": c.difficulty,
                    "rating": c.rating,
                    "enrolled_count": c.enrolled_count,
                    "source": c.source,
                    "category": c.category
                } for c in popular_courses
            ]
        }

    profile = current_user.profile

    # ═════════════════════════════════════════════════════════════════════
    # 1. CONTINUE LEARNING (Dynamically derived from latest learner state)
    # ═════════════════════════════════════════════════════════════════════
    # Find the most recently active enrollment for this learner.
    # We rank enrollments by:
    # 1. Most recent progress update in that enrollment
    # 2. Most recent viewed course in learning history
    # 3. Started date
    user_enrollments = (
        db.query(Enrollment)
        .options(
            joinedload(Enrollment.course).selectinload(Course.modules).selectinload(Module.lessons),
            selectinload(Enrollment.progress_records)
        )
        .filter(Enrollment.user_id == current_user.id)
        .all()
    )

    # Map each course to its latest learning history viewed_at
    lh_records = (
        db.query(LearningHistory)
        .filter(LearningHistory.user_id == current_user.id)
        .order_by(LearningHistory.viewed_at.desc())
        .all()
    )
    course_last_viewed: Dict[int, datetime.datetime] = {}
    for lh in lh_records:
        if lh.course_id not in course_last_viewed:
            course_last_viewed[lh.course_id] = lh.viewed_at

    def enrollment_recency_key(enr: Enrollment) -> datetime.datetime:
        # Latest progress update timestamp
        latest_prog = max(
            (p.updated_at for p in enr.progress_records if p.updated_at),
            default=None
        )
        latest_view = course_last_viewed.get(enr.course_id)
        candidates = [t for t in [latest_prog, latest_view, enr.started_at] if t is not None]
        return max(candidates) if candidates else datetime.datetime.min

    # Sort enrollments by recency (most recent first)
    sorted_enrollments = sorted(user_enrollments, key=enrollment_recency_key, reverse=True)

    # Prefer an incomplete course first (progress < 100 or status == 'in_progress')
    active_enrollment = next(
        (e for e in sorted_enrollments if e.progress_percent < 100.0 or e.status == "in_progress"),
        sorted_enrollments[0] if sorted_enrollments else None
    )

    continue_learning = None
    if active_enrollment and active_enrollment.course:
        course = active_enrollment.course
        
        # Flatten lessons in course order
        all_course_lessons = []
        for mod in sorted(course.modules, key=lambda m: m.order):
            for les in sorted(mod.lessons, key=lambda l: l.order):
                all_course_lessons.append(les)

        completed_lesson_ids = {
            p.lesson_id for p in active_enrollment.progress_records if p.completed
        }

        # Calculate exact progress percent
        total_lessons_count = len(all_course_lessons)
        actual_progress = (
            round((len(completed_lesson_ids) / max(total_lessons_count, 1)) * 100, 1)
            if total_lessons_count > 0 else 0.0
        )
        active_enrollment.progress_percent = actual_progress
        if actual_progress >= 100.0 and active_enrollment.status != "completed":
            active_enrollment.status = "completed"
            active_enrollment.completed_at = datetime.datetime.utcnow()

        # Find current target lesson
        # If last_lesson_id is set and not completed, use it; otherwise find first incomplete lesson
        target_lesson = None
        if active_enrollment.last_lesson_id:
            last_les = next((l for l in all_course_lessons if l.id == active_enrollment.last_lesson_id), None)
            if last_les and last_les.id not in completed_lesson_ids:
                target_lesson = last_les

        if not target_lesson:
            target_lesson = next((l for l in all_course_lessons if l.id not in completed_lesson_ids), None)

        # If all lessons are completed, fallback to the last lesson
        if not target_lesson and all_course_lessons:
            target_lesson = all_course_lessons[-1]

        continue_learning = {
            "enrollment_id": active_enrollment.id,
            "course_id": course.id,
            "course_title": course.title,
            "organization": course.organization,
            "progress_percent": actual_progress,
            "current_module": target_lesson.module.title if (target_lesson and target_lesson.module) else (course.modules[0].title if course.modules else "Module 1"),
            "current_lesson": target_lesson.title if target_lesson else "Course Orientation",
            "last_lesson_id": target_lesson.id if target_lesson else None,
            "is_completed": actual_progress >= 100.0,
            "button_label": "Resume Lesson" if actual_progress > 0 else "Start Learning"
        }

    # ═════════════════════════════════════════════════════════════════════
    # 2. TODAY'S LEARNING GOAL (Calculated from actual today's learning)
    # ═════════════════════════════════════════════════════════════════════
    now = datetime.datetime.utcnow()
    today_start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    
    # Sum durations of lessons interacted with or completed today
    today_progress_records = (
        db.query(Progress)
        .join(Enrollment, Progress.enrollment_id == Enrollment.id)
        .filter(Enrollment.user_id == current_user.id, Progress.updated_at >= today_start)
        .all()
    )
    
    lesson_ids_today = {p.lesson_id for p in today_progress_records}
    today_lessons = db.query(Lesson).filter(Lesson.id.in_(lesson_ids_today)).all() if lesson_ids_today else []
    today_lesson_minutes = sum(l.duration_minutes or 15 for l in today_lessons)
    
    # Include assessment attempts submitted today (estimated 20 minutes each)
    today_attempts_count = (
        db.query(AssessmentAttempt)
        .filter(AssessmentAttempt.user_id == current_user.id, AssessmentAttempt.submitted_at >= today_start)
        .count()
    )
    today_attempt_minutes = today_attempts_count * 20
    
    today_completed_minutes = today_lesson_minutes + today_attempt_minutes
    daily_goal_minutes = profile.daily_goal_minutes if (profile and profile.daily_goal_minutes) else 30
    goal_percent = min(100, int((today_completed_minutes / max(daily_goal_minutes, 1)) * 100))

    # ═════════════════════════════════════════════════════════════════════
    # 3. LEARNING STREAK (Calculated from actual activity dates)
    # ═════════════════════════════════════════════════════════════════════
    # Collect all unique dates where user completed/updated progress, viewed a lesson, or took an assessment
    progress_dates = {
        row[0] for row in db.query(func.date(Progress.updated_at))
        .join(Enrollment, Progress.enrollment_id == Enrollment.id)
        .filter(Enrollment.user_id == current_user.id)
        .all() if row[0]
    }
    history_dates = {
        row[0] for row in db.query(func.date(LearningHistory.viewed_at))
        .filter(LearningHistory.user_id == current_user.id)
        .all() if row[0]
    }
    attempt_dates = {
        row[0] for row in db.query(func.date(AssessmentAttempt.submitted_at))
        .filter(AssessmentAttempt.user_id == current_user.id)
        .all() if row[0]
    }

    # Normalize all to datetime.date
    all_raw_dates = progress_dates | history_dates | attempt_dates
    active_dates = set()
    for d in all_raw_dates:
        if isinstance(d, datetime.date):
            active_dates.add(d)
        elif isinstance(d, str):
            try:
                active_dates.add(datetime.date.fromisoformat(d.split("T")[0]))
            except Exception:
                pass

    today_date = now.date()
    yesterday_date = today_date - datetime.timedelta(days=1)

    streak_days = 0
    if today_date in active_dates:
        cur = today_date
        while cur in active_dates:
            streak_days += 1
            cur -= datetime.timedelta(days=1)
    elif yesterday_date in active_dates:
        cur = yesterday_date
        while cur in active_dates:
            streak_days += 1
            cur -= datetime.timedelta(days=1)
    else:
        streak_days = 0

    if profile:
        profile.current_streak_days = streak_days

    # ═════════════════════════════════════════════════════════════════════
    # 4. PREVIOUSLY LEARNED / RECENT LEARNING HISTORY
    # ═════════════════════════════════════════════════════════════════════
    recent_history_records = (
        db.query(LearningHistory)
        .options(joinedload(LearningHistory.course))
        .filter(LearningHistory.user_id == current_user.id)
        .order_by(LearningHistory.viewed_at.desc())
        .all()
    )
    
    # Deduplicate by course preserving most recent order
    seen_course_ids = set()
    recently_explored = []
    for h in recent_history_records:
        if h.course and h.course.id not in seen_course_ids:
            seen_course_ids.add(h.course.id)
            recently_explored.append({
                "id": h.course.id,
                "title": h.course.title,
                "organization": h.course.organization,
                "duration_hours": h.course.duration_hours,
                "difficulty": h.course.difficulty,
                "rating": h.course.rating,
                "category": h.course.category,
                "viewed_at": h.viewed_at.isoformat()
            })
            if len(recently_explored) == 3:
                break

    # If recent history is empty, populate from enrolled courses
    if not recently_explored:
        for enr in sorted_enrollments[:3]:
            if enr.course:
                recently_explored.append({
                    "id": enr.course.id,
                    "title": enr.course.title,
                    "organization": enr.course.organization,
                    "duration_hours": enr.course.duration_hours,
                    "difficulty": enr.course.difficulty,
                    "rating": enr.course.rating,
                    "category": enr.course.category,
                    "viewed_at": enr.started_at.isoformat()
                })

    # ═════════════════════════════════════════════════════════════════════
    # 5. RECOMMENDED FOR YOUR MINISTRY (Dynamic, uncompleted courses)
    # ═════════════════════════════════════════════════════════════════════
    completed_course_ids = {
        e.course_id for e in user_enrollments if e.progress_percent >= 100.0 or e.status == "completed"
    }
    
    # AI-curated pending recommendations first
    ai_recs = (
        db.query(Course)
        .join(Recommendation, Recommendation.course_id == Course.id)
        .filter(Recommendation.user_id == current_user.id, Recommendation.status == "pending")
        .order_by(Recommendation.score.desc())
        .all()
    )

    all_catalog_courses = db.query(Course).order_by(Course.rating.desc(), Course.enrolled_count.desc()).all()
    
    recommended_courses: List[Course] = []
    # 1. AI recommendations that are not completed
    for c in ai_recs:
        if c.id not in completed_course_ids and all(c.id != x.id for x in recommended_courses):
            recommended_courses.append(c)

    # 2. Ministry / Cadre aligned catalog courses not yet completed
    user_dept_str = (profile.department or "").lower() if profile else ""
    for c in all_catalog_courses:
        if c.id not in completed_course_ids and all(c.id != x.id for x in recommended_courses):
            # Prioritize matching category
            if any(term in user_dept_str for term in ["stat", "cso", "nsso", "mospi"]) and c.category in ["Statistical", "Technical"]:
                recommended_courses.append(c)
            elif "personnel" in user_dept_str or "dopt" in user_dept_str and c.category == "Behavioural":
                recommended_courses.append(c)
            elif "governance" in user_dept_str or "meity" in user_dept_str and c.category == "Digital Governance":
                recommended_courses.append(c)

    # 3. Top up with remaining courses
    for c in all_catalog_courses:
        if c.id not in completed_course_ids and all(c.id != x.id for x in recommended_courses):
            recommended_courses.append(c)
        if len(recommended_courses) >= RECOMMENDED_COURSE_COUNT:
            break

    # If all courses are completed, show top catalog courses for revision
    if not recommended_courses:
        recommended_courses = all_catalog_courses[:RECOMMENDED_COURSE_COUNT]

    # ═════════════════════════════════════════════════════════════════════
    # 6. TRENDING COURSES (Derived from actual enrollment metrics)
    # ═════════════════════════════════════════════════════════════════════
    trending_courses = db.query(Course).order_by(Course.enrolled_count.desc(), Course.rating.desc()).limit(4).all()

    # ═════════════════════════════════════════════════════════════════════
    # 7. FUTURE PLANNED COURSES (Real PlannedCourse records)
    # ═════════════════════════════════════════════════════════════════════
    planned_records = (
        db.query(PlannedCourse)
        .options(joinedload(PlannedCourse.course))
        .filter(PlannedCourse.user_id == current_user.id)
        .all()
    )
    future_planned = [
        {
            "id": p.id,
            "course_id": p.course.id,
            "course_title": p.course.title,
            "organization": p.course.organization,
            "duration_hours": p.course.duration_hours,
            "planned_for": p.planned_for or "Upcoming Quarter",
            "source": p.source
        }
        for p in planned_records if p.course
    ]

    # ═════════════════════════════════════════════════════════════════════
    # 8. LEARNING METRICS & SKILLS BREAKDOWN
    # ═════════════════════════════════════════════════════════════════════
    in_progress_count = sum(1 for e in user_enrollments if e.status == "in_progress" and e.progress_percent < 100.0)
    completed_count = sum(1 for e in user_enrollments if e.status == "completed" or e.progress_percent >= 100.0)
    overall_progress = (
        round(sum(e.progress_percent for e in user_enrollments) / max(len(user_enrollments), 1), 1)
        if user_enrollments else 0.0
    )

    # Calculate actual learned hours from completed lessons
    completed_progress_all = (
        db.query(Progress)
        .join(Enrollment, Progress.enrollment_id == Enrollment.id)
        .filter(Enrollment.user_id == current_user.id, Progress.completed == True)
        .all()
    )
    completed_lesson_ids_all = {p.lesson_id for p in completed_progress_all}
    if completed_lesson_ids_all:
        completed_lessons = db.query(Lesson).filter(Lesson.id.in_(completed_lesson_ids_all)).all()
        total_completed_minutes = sum(l.duration_minutes or 15 for l in completed_lessons)
        hours_learned = round(total_completed_minutes / 60.0, 1)
    else:
        hours_learned = 0.0

    user_skills = (
        db.query(UserSkill)
        .options(joinedload(UserSkill.skill))
        .filter(UserSkill.user_id == current_user.id)
        .all()
    )
    skills_list = [
        {
            "id": us.skill.id,
            "name": us.skill.name,
            "category": us.skill.category,
            "acquired_at": us.acquired_at.strftime("%b %Y") if us.acquired_at else "Recently"
        }
        for us in user_skills if us.skill
    ]

    db.commit()

    return {
        "authenticated": True,
        "learner": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "designation": profile.designation if profile else "Civil Servant",
            "department": profile.department if profile else "Official Statistical System",
            "role": current_user.role
        },
        "continue_learning": continue_learning,
        "todays_goals": {
            "target_minutes": daily_goal_minutes,
            "achieved_minutes": today_completed_minutes,
            "percent": goal_percent
        },
        "learning_streak": {
            "streak_days": streak_days,
            "last_active": profile.last_active_date.isoformat() if profile and profile.last_active_date else None
        },
        "my_learning_progress": {
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,
            "overall_progress_percent": overall_progress,
            "hours_learned": hours_learned
        },
        "competencies": {
            "skills_count": len(skills_list),
            "top_skills": skills_list
        },
        "recently_explored": recently_explored,
        "trending_courses": [
            {
                "id": c.id,
                "title": c.title,
                "overview": c.overview,
                "organization": c.organization,
                "duration_hours": c.duration_hours,
                "difficulty": c.difficulty,
                "enrolled_count": c.enrolled_count,
                "rating": c.rating,
                "source": c.source,
                "category": c.category
            }
            for c in trending_courses
        ],
        "recommended_courses": [
            {
                "id": c.id,
                "title": c.title,
                "overview": c.overview,
                "organization": c.organization,
                "duration_hours": c.duration_hours,
                "difficulty": c.difficulty,
                "enrolled_count": c.enrolled_count,
                "rating": c.rating,
                "source": c.source,
                "category": c.category
            }
            for c in recommended_courses
        ],
        "future_planned": future_planned
    }
