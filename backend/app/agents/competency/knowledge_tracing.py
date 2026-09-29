import datetime
import json
import logging
import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    User, UserProfile, Course, Module, Lesson, Enrollment, Progress,
    Assessment, AssessmentAttempt, Question,
    CompetencyDomain, Competency, UserCompetencyScore, GapAnalysis,
    CompetencyProfile, Recommendation,
    StatEngineAttempt, StatEngineMastery,
    BehaviouralSessionResult,
    CyberSandboxSession, CyberSandboxChallenge,
    GeneratedQuiz, GeneratedQuizQuestion, QuizAttempt,
    TechnicalGeneratedLab,
)
from app.agents.competency.target_levels import resolve_target_level

logger = logging.getLogger("knowledge_tracing")

# Modality base confidence weights
ACTIVITY_WEIGHTS = {
    "lab_execution": 1.5,       # Verified sandboxed code execution
    "cyber_sandbox": 1.4,      # Hands-on CTF/incident defense challenge
    "certification_exam": 1.3, # Official course certification assessment
    "ai_interview": 1.25,      # Oral Board / Behavioural AI interrogation
    "case_inquiry": 1.2,       # Quasi-judicial departmental inquiry simulation
    "stat_question": 1.1,      # Adaptive statistical computation / chart interpretation
    "quiz_attempt": 1.0,       # Custom or material-generated quiz
    "in_lesson_check": 0.85,   # Embedded micro-activity check in video lesson
    "lesson_completed": 0.6,   # Reading / lecture completion
    "self_declared": 0.5,      # Initial onboarding profile claim
}

# Decay constant (lambda): 30-day half-life for exponential recency weighting
DECAY_LAMBDA = 0.025


# Comprehensive taxonomy map linking course/lab/quiz topic keywords to competency codes
TOPIC_TO_COMPETENCY_CODE = {
    # 1. Statistical Domain
    "price_statistics": "statistical_price_statistics",
    "cpi": "statistical_price_statistics",
    "inflation": "statistical_price_statistics",
    "laspeyres": "statistical_price_statistics",
    "jevons": "statistical_price_statistics",
    "index": "statistical_price_statistics",
    "survey": "statistical_survey_design",
    "sampling": "statistical_sampling",
    "sample": "statistical_sampling",
    "nsso": "statistical_survey_design",
    "national_accounts": "statistical_national_accounts",
    "gdp": "statistical_national_accounts",
    "quality": "statistical_data_quality",
    "validation": "statistical_data_quality",
    "data_quality": "statistical_data_quality",
    "sdg": "statistical_sdg_indicators",
    "metadata": "statistical_metadata_standards",
    "agricultural": "statistical_agricultural_statistics",
    "industrial": "statistical_industrial_statistics",
    "labour": "statistical_labour_statistics",

    # 2. Technical Domain
    "python": "technical_python",
    "pandas": "technical_python",
    "dataframe": "technical_python",
    "data cleaning": "technical_python",
    "debugging": "technical_python",
    "vectorized": "technical_python",
    "data_visualization": "technical_data_visualization",
    "visualization": "technical_data_visualization",
    "chart": "technical_data_visualization",
    "matplotlib": "technical_data_visualization",
    "sql": "technical_sql",
    "query": "technical_sql",
    "api": "technical_apis",
    "fastapi": "technical_apis",
    "pydantic": "technical_apis",
    "rest": "technical_apis",
    "ai": "technical_ai_ml",
    "ml": "technical_ai_ml",
    "machine_learning": "technical_ai_ml",
    "gis": "technical_gis",
    "spatial": "technical_gis",
    "open_data": "technical_open_data",
    "r": "technical_r",
    "stata": "technical_stata",
    "cloud": "technical_cloud_computing",

    # 3. Digital Governance Domain
    "cyber": "digital_governance_cybersecurity",
    "cybersecurity": "digital_governance_cybersecurity",
    "soc": "digital_governance_cybersecurity",
    "incident": "digital_governance_cybersecurity",
    "malware": "digital_governance_cybersecurity",
    "forensics": "digital_governance_digital_forensics",
    "investigation": "digital_governance_digital_forensics",
    "privacy": "digital_governance_data_privacy",
    "dpdp": "digital_governance_data_privacy",
    "gdpr": "digital_governance_data_privacy",
    "dpi": "digital_governance_dpi",
    "aadhaar": "digital_governance_dpi",
    "api_setu": "digital_governance_dpi",
    "cloud_gov": "digital_governance_gov_cloud",
    "meghraj": "digital_governance_gov_cloud",
    "signature": "digital_governance_digital_signatures",
    "pki": "digital_governance_digital_signatures",

    # 4. Behavioural & Managerial Domain
    "leadership": "behavioural_leadership",
    "management": "behavioural_leadership",
    "ethics": "behavioural_ethics",
    "conduct": "behavioural_ethics",
    "integrity": "behavioural_ethics",
    "conflict_of_interest": "behavioural_ethics",
    "decision_making": "behavioural_decision_making",
    "disciplinary": "behavioural_decision_making",
    "inquiry": "behavioural_decision_making",
    "quasi_judicial": "behavioural_decision_making",
    "communication": "behavioural_communication",
    "stakeholder": "behavioural_communication",
    "situational_awareness": "behavioural_situational_awareness",
    "crisis": "behavioural_situational_awareness",
    "accountability": "behavioural_accountability",
    "vigilance": "behavioural_accountability",
    "change_management": "behavioural_change_management",
    "project_management": "behavioural_project_management",
}


def map_text_to_competency_code(text: Optional[str], default_domain: Optional[str] = None) -> Optional[str]:
    """Matches free text or topic tag to a canonical competency code."""
    if not text:
        return None
    cleaned = text.lower().replace("-", " ").replace("_", " ")
    for keyword, code in TOPIC_TO_COMPETENCY_CODE.items():
        kw_clean = keyword.replace("_", " ")
        if kw_clean in cleaned:
            return code
    if default_domain:
        # Fallback to first competency in domain
        return f"{default_domain}_general"
    return None


class KnowledgeInteraction:
    def __init__(
        self,
        competency_code: str,
        activity_type: str,
        score_ratio: float,  # 0.0 to 1.0
        timestamp: datetime.datetime,
        activity_title: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.competency_code = competency_code
        self.activity_type = activity_type
        self.score_ratio = max(0.0, min(1.0, float(score_ratio)))
        self.timestamp = timestamp or datetime.datetime.utcnow()
        self.activity_title = activity_title
        self.metadata = metadata or {}


class AttentiveKnowledgeTracingEngine:
    """
    Real-Time Attentive Knowledge Tracing (AKT) Engine.
    
    Collects heterogeneous learner interaction signals, applies recency-decayed
    attention weighting, evaluates topic/competency-level mastery, and triggers
    skill gap and personalized recommendation refreshes.
    """

    @classmethod
    def collect_all_user_interactions(cls, db: Session, user_id: int) -> List[KnowledgeInteraction]:
        """Harvests all historical interactions across learning player, quizzes, labs, exams, and sandboxes."""
        interactions: List[KnowledgeInteraction] = []
        now = datetime.datetime.utcnow()

        # 1. Lesson completions & In-lesson Activity Checks
        progress_records = (
            db.query(Progress)
            .join(Enrollment, Progress.enrollment_id == Enrollment.id)
            .filter(Enrollment.user_id == user_id)
            .all()
        )
        for p in progress_records:
            lesson = db.query(Lesson).filter_by(id=p.lesson_id).first()
            if not lesson:
                continue
            comp_code = map_text_to_competency_code(lesson.topic or lesson.title)
            if not comp_code and lesson.module and lesson.module.course:
                comp_code = map_text_to_competency_code(lesson.module.course.title)

            if comp_code:
                # Lesson completed
                if p.completed:
                    interactions.append(KnowledgeInteraction(
                        competency_code=comp_code,
                        activity_type="lesson_completed",
                        score_ratio=1.0,
                        timestamp=p.updated_at or now,
                        activity_title=f"Lesson: {lesson.title}",
                        metadata={"lesson_id": lesson.id, "duration": lesson.duration_minutes}
                    ))
                # In-lesson practice activity
                if p.activity_completed:
                    interactions.append(KnowledgeInteraction(
                        competency_code=comp_code,
                        activity_type="in_lesson_check",
                        score_ratio=1.0,
                        timestamp=p.updated_at or now,
                        activity_title=f"Lesson Check: {lesson.title}",
                        metadata={"lesson_id": lesson.id}
                    ))

        # 2. Certification Assessment Attempts
        assessment_attempts = db.query(AssessmentAttempt).filter_by(user_id=user_id).all()
        for aa in assessment_attempts:
            course = aa.assessment.course if aa.assessment else None
            comp_code = map_text_to_competency_code(course.title if course else "Assessment")
            if comp_code:
                interactions.append(KnowledgeInteraction(
                    competency_code=comp_code,
                    activity_type="certification_exam",
                    score_ratio=aa.score_percent / 100.0,
                    timestamp=aa.submitted_at or now,
                    activity_title=f"Exam: {aa.assessment.title if aa.assessment else 'Certification Assessment'}",
                    metadata={"score_percent": aa.score_percent, "passed": aa.passed}
                ))

        # 3. Adaptive Statistical Engine Attempts & Mastery
        stat_attempts = db.query(StatEngineAttempt).filter_by(user_id=str(user_id)).all()
        for sa in stat_attempts:
            comp_code = "statistical_price_statistics" if "price" in sa.skill_id else map_text_to_competency_code(sa.skill_id)
            if comp_code:
                score = 1.0 if sa.is_correct else max(0.0, sa.score / 100.0 if sa.score > 1.0 else sa.score)
                interactions.append(KnowledgeInteraction(
                    competency_code=comp_code,
                    activity_type="stat_question",
                    score_ratio=score,
                    timestamp=sa.created_at or now,
                    activity_title=f"Statistical Question: {sa.skill_id}",
                    metadata={"time_taken": sa.time_taken_seconds, "correct": sa.is_correct}
                ))

        stat_mastery_records = db.query(StatEngineMastery).filter_by(user_id=str(user_id)).all()
        for sm in stat_mastery_records:
            comp_code = "statistical_price_statistics" if "price" in sm.skill_id else map_text_to_competency_code(sm.skill_id)
            if comp_code:
                try:
                    data = json.loads(sm.mastery_json) if sm.mastery_json else {}
                    score_val = data.get("score", 60.0)
                except Exception:
                    score_val = 60.0
                interactions.append(KnowledgeInteraction(
                    competency_code=comp_code,
                    activity_type="stat_question",
                    score_ratio=float(score_val) / 100.0,
                    timestamp=sm.updated_at or now,
                    activity_title=f"Statistical Assessment: {sm.skill_id}",
                    metadata={"score": score_val}
                ))

        # 4. Material Quizzes & Quiz Attempts
        quiz_attempts = db.query(QuizAttempt).filter_by(user_id=user_id).all()
        for qa in quiz_attempts:
            quiz = qa.quiz
            comp_code = map_text_to_competency_code(quiz.title if quiz else "Quiz")
            if comp_code:
                interactions.append(KnowledgeInteraction(
                    competency_code=comp_code,
                    activity_type="quiz_attempt",
                    score_ratio=qa.score_percent / 100.0,
                    timestamp=qa.submitted_at or now,
                    activity_title=f"Quiz: {quiz.title if quiz else 'Topic Quiz'}",
                    metadata={"score_percent": qa.score_percent, "correct": qa.correct_count, "total": qa.total_questions}
                ))

        # 5. Cybersecurity Sandbox Sessions
        cyber_sessions = db.query(CyberSandboxSession).filter_by(user_id=user_id).all()
        for cs in cyber_sessions:
            challenge = cs.challenge
            comp_id = challenge.competency_id if challenge else "soc_investigation"
            comp_code = (
                "digital_governance_cybersecurity" if comp_id in ["soc_investigation", "threat_intel"]
                else "digital_governance_digital_forensics" if comp_id == "digital_forensics"
                else "digital_governance_data_privacy" if comp_id == "data_privacy"
                else "digital_governance_gov_cloud" if comp_id == "cloud_security"
                else "digital_governance_cybersecurity"
            )
            score_ratio = (cs.final_score / max(1, challenge.points)) if (challenge and cs.is_solved) else (1.0 if cs.is_solved else 0.2)
            interactions.append(KnowledgeInteraction(
                competency_code=comp_code,
                activity_type="cyber_sandbox",
                score_ratio=score_ratio,
                timestamp=cs.solved_at or cs.created_at or now,
                activity_title=f"Cyber Sandbox: {challenge.title if challenge else 'Incident Challenge'}",
                metadata={"solved": cs.is_solved, "points": cs.final_score}
            ))

        # 6. Behavioural AI Interviews & Case Study Inquiries
        behav_results = db.query(BehaviouralSessionResult).filter_by(user_id=user_id).all()
        for br in behav_results:
            try:
                res_data = json.loads(br.result_json) if br.result_json else {}
            except Exception:
                res_data = {}
            comp_scores = res_data.get("competency_scores", {})
            for name, score_val in comp_scores.items():
                comp_code = (
                    "behavioural_ethics" if name in ["Ethics", "Ethical Judgement"]
                    else "behavioural_leadership" if name == "Leadership"
                    else "behavioural_decision_making" if name == "Decision Making"
                    else "behavioural_communication" if name == "Communication"
                    else "behavioural_situational_awareness" if name == "Situational Awareness"
                    else "behavioural_accountability" if name == "Accountability"
                    else "behavioural_ethics"
                )
                val = score_val.get("score_percent") if isinstance(score_val, dict) else score_val
                if val is not None:
                    interactions.append(KnowledgeInteraction(
                        competency_code=comp_code,
                        activity_type="ai_interview" if br.session_type == "interview" else "case_inquiry",
                        score_ratio=float(val) / 100.0,
                        timestamp=br.completed_at or now,
                        activity_title=f"Behavioural {br.session_type.capitalize()}: {name}",
                        metadata={"score": val}
                    ))

        return interactions

    @classmethod
    def compute_mastery_and_gaps(cls, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Executes AKT mathematical formulation across all learner evidence.
        Updates UserCompetencyScore, CompetencyProfile, and GapAnalysis tables.
        """
        now = datetime.datetime.utcnow()
        user = db.query(User).filter_by(id=user_id).first()
        profile_row = user.profile if user else None

        # Resolve role target level
        target_level = resolve_target_level(
            profile_row.designation if profile_row else None,
            profile_row.job_role if profile_row else None,
        )

        all_competencies = db.query(Competency).options(joinedload(Competency.domain)).all()
        comp_by_code: Dict[str, Competency] = {c.code: c for c in all_competencies}
        comp_by_id: Dict[int, Competency] = {c.id: c for c in all_competencies}

        # Gather interactions
        interactions = cls.collect_all_user_interactions(db, user_id)
        interactions_by_comp: Dict[str, List[KnowledgeInteraction]] = defaultdict(list)
        for act in interactions:
            interactions_by_comp[act.competency_code].append(act)

        # Baseline declared scores from UserCompetencyScore
        declared_rows = db.query(UserCompetencyScore).filter_by(user_id=user_id).all()
        declared_by_comp_id = {row.competency_id: row.level for row in declared_rows}

        computed_levels: Dict[int, float] = {}
        mastery_percentages: Dict[int, float] = {}
        competency_evidence_counts: Dict[int, int] = {}
        competency_recent_evidence: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

        for comp in all_competencies:
            comp_acts = interactions_by_comp.get(comp.code, [])
            competency_evidence_counts[comp.id] = len(comp_acts)

            if not comp_acts:
                # Fallback to prior declared level or default base
                base_level = declared_by_comp_id.get(comp.id, 2.0)
                computed_levels[comp.id] = base_level
                mastery_percentages[comp.id] = round((base_level / 5.0) * 100.0, 1)
                continue

            # Sort chronological
            comp_acts.sort(key=lambda a: a.timestamp)

            # Store up to 3 recent evidence snippets
            for act in reversed(comp_acts[-3:]):
                competency_recent_evidence[comp.id].append({
                    "title": act.activity_title,
                    "type": act.activity_type.replace("_", " ").title(),
                    "score_pct": round(act.score_ratio * 100.0, 1),
                    "date": act.timestamp.strftime("%d %b %Y"),
                })

            # Attentive Exponential Decay Sum
            total_weight = 0.0
            weighted_score_sum = 0.0
            streak = 0

            for act in comp_acts:
                days_ago = max(0.0, (now - act.timestamp).total_seconds() / 86400.0)
                base_w = ACTIVITY_WEIGHTS.get(act.activity_type, 1.0)
                time_w = base_w * math.exp(-DECAY_LAMBDA * days_ago)

                weighted_score_sum += time_w * act.score_ratio
                total_weight += time_w

                if act.score_ratio >= 0.70:
                    streak += 1
                else:
                    streak = 0

            raw_mastery = weighted_score_sum / max(total_weight, 0.001)

            # Recency momentum: repeated success solidifies mastery
            if streak >= 2:
                raw_mastery = min(1.0, raw_mastery * (1.0 + 0.05 * min(streak, 3)))
            elif comp_acts and comp_acts[-1].score_ratio < 0.50:
                # Sensitive attentive penalty on recent failed attempt
                raw_mastery = max(0.05, raw_mastery - 0.12 * (1.0 - comp_acts[-1].score_ratio))

            final_mastery = max(0.05, min(1.0, raw_mastery))
            calculated_level = round(final_mastery * 5.0, 2)

            if any(a.activity_type in ["certification_exam", "stat_question", "quiz_attempt"] for a in comp_acts):
                ev_source = "assessment"
            elif any(a.activity_type in ["lab_execution", "cyber_sandbox"] for a in comp_acts):
                ev_source = "lab"
            elif any(a.activity_type in ["ai_interview", "case_inquiry"] for a in comp_acts):
                ev_source = "simulation"
            elif comp_acts:
                ev_source = "course"
            else:
                ev_source = "declared"

            # Persist / Upsert UserCompetencyScore
            score_row = next((r for r in declared_rows if r.competency_id == comp.id), None)
            if not score_row:
                score_row = UserCompetencyScore(
                    user_id=user_id,
                    competency_id=comp.id,
                    level=calculated_level,
                    evidence_source=ev_source,
                    updated_at=now,
                )
                db.add(score_row)
            else:
                score_row.level = calculated_level
                score_row.evidence_source = ev_source
                score_row.updated_at = now

            computed_levels[comp.id] = calculated_level
            mastery_percentages[comp.id] = round(final_mastery * 100.0, 1)

        # Domain Aggregations & Gap Analysis
        domains = db.query(CompetencyDomain).all()
        gaps: List[GapAnalysis] = []
        domain_scores: Dict[str, float] = {}

        for domain in domains:
            domain_comp_ids = [c.id for c in all_competencies if c.domain_id == domain.id]
            levels_in_domain = [computed_levels[cid] for cid in domain_comp_ids if cid in computed_levels]
            domain_current_level = (
                round(sum(levels_in_domain) / len(levels_in_domain), 2)
                if levels_in_domain else 0.0
            )
            gap_value = max(0.0, round(target_level - domain_current_level, 2))

            gap_record = db.query(GapAnalysis).filter_by(user_id=user_id, domain_id=domain.id).first()
            if not gap_record:
                gap_record = GapAnalysis(
                    user_id=user_id,
                    domain_id=domain.id,
                    target_level=target_level,
                    current_level=domain_current_level,
                    gap=gap_value,
                    generated_at=now,
                )
                db.add(gap_record)
            else:
                gap_record.target_level = target_level
                gap_record.current_level = domain_current_level
                gap_record.gap = gap_value
                gap_record.generated_at = now
            gaps.append(gap_record)

            domain_score_pct = round((domain_current_level / 5.0) * 100.0, 1)
            domain_scores[domain.code] = domain_score_pct

        # Update CompetencyProfile
        profile = db.query(CompetencyProfile).filter_by(user_id=user_id).first()
        if not profile:
            profile = CompetencyProfile(user_id=user_id)
            db.add(profile)

        profile.statistical_score = domain_scores.get("statistical", 0.0)
        profile.technical_score = domain_scores.get("technical", 0.0)
        profile.digital_governance_score = domain_scores.get("digital_governance", 0.0)
        profile.behavioural_score = domain_scores.get("behavioural", 0.0)
        profile.last_computed_at = now

        db.commit()

        return {
            "target_level": target_level,
            "profile": profile,
            "gaps": gaps,
            "computed_levels": computed_levels,
            "mastery_percentages": mastery_percentages,
            "evidence_counts": competency_evidence_counts,
            "recent_evidence": competency_recent_evidence,
            "total_interactions": len(interactions),
        }

    @classmethod
    def get_full_traceable_profile(cls, db: Session, user_id: int) -> Dict[str, Any]:
        """Returns rich, verifiable skill intelligence for the learner dashboard and competency pages."""
        analysis = cls.compute_mastery_and_gaps(db, user_id)
        target_level = analysis["target_level"]
        computed_levels = analysis["computed_levels"]
        mastery_percentages = analysis["mastery_percentages"]
        evidence_counts = analysis["evidence_counts"]
        recent_evidence = analysis["recent_evidence"]

        all_competencies = db.query(Competency).options(joinedload(Competency.domain)).all()
        competencies_list = []

        score_rows = db.query(UserCompetencyScore).filter_by(user_id=user_id).all()
        evidence_source_by_comp_id = {r.competency_id: r.evidence_source for r in score_rows}

        for comp in all_competencies:
            level = computed_levels.get(comp.id, 2.0)
            mastery_pct = mastery_percentages.get(comp.id, round((level / 5.0) * 100.0, 1))
            gap = max(0.0, round(target_level - level, 2))

            # Classification: Strong / Developing / Gap
            if level >= target_level or mastery_pct >= 80.0:
                status = "Strong"
                status_color = "emerald"
            elif level >= target_level - 1.0 or mastery_pct >= 50.0:
                status = "Developing"
                status_color = "amber"
            else:
                status = "Gap"
                status_color = "rose"

            competencies_list.append({
                "id": comp.id,
                "code": comp.code,
                "name": comp.name,
                "domain_code": comp.domain.code if comp.domain else "general",
                "domain_name": comp.domain.name if comp.domain else "General",
                "level": level,
                "target_level": target_level,
                "mastery_percent": mastery_pct,
                "gap": gap,
                "status": status,
                "status_color": status_color,
                "evidence_source": evidence_source_by_comp_id.get(comp.id, "declared"),
                "evidence_count": evidence_counts.get(comp.id, 0),
                "recent_evidence": recent_evidence.get(comp.id, []),
            })

        # Sort competencies by largest gap first
        competencies_list.sort(key=lambda c: (-c["gap"], c["mastery_percent"]))

        domain_summaries = []
        for gap in analysis["gaps"]:
            domain_comps = [c for c in competencies_list if c["domain_code"] == gap.domain.code]
            strong_count = sum(1 for c in domain_comps if c["status"] == "Strong")
            developing_count = sum(1 for c in domain_comps if c["status"] == "Developing")
            gap_count = sum(1 for c in domain_comps if c["status"] == "Gap")

            domain_summaries.append({
                "code": gap.domain.code,
                "name": gap.domain.name,
                "current_level": gap.current_level,
                "target_level": gap.target_level,
                "gap": gap.gap,
                "score_percent": round((gap.current_level / 5.0) * 100.0, 1),
                "strong_count": strong_count,
                "developing_count": developing_count,
                "gap_count": gap_count,
                "competency_count": len(domain_comps),
            })

        return {
            "target_level": target_level,
            "overall_average_level": round(
                sum(c["level"] for c in competencies_list) / max(len(competencies_list), 1), 2
            ),
            "domains": domain_summaries,
            "competencies": competencies_list,
            "total_interactions_traced": analysis["total_interactions"],
            "last_traced_at": datetime.datetime.utcnow().isoformat(),
        }

    @classmethod
    def generate_intelligent_recommendations(cls, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Generates multi-tier, verifiable recommendations across courses, labs, quizzes, and revisions
        based on active skill gaps and uncompleted activities.
        """
        profile = cls.get_full_traceable_profile(db, user_id)
        gap_competencies = [c for c in profile["competencies"] if c["gap"] > 0 or c["status"] != "Strong"]
        if not gap_competencies:
            # If all are strong, look for lowest mastery
            gap_competencies = sorted(profile["competencies"], key=lambda c: c["mastery_percent"])[:3]

        # Get completed course IDs
        completed_enrollments = db.query(Enrollment).filter_by(user_id=user_id, status="completed").all()
        completed_course_ids = {e.course_id for e in completed_enrollments}

        # Clear existing pending recommendations
        db.query(Recommendation).filter_by(user_id=user_id, status="pending").delete()

        recommendations_output = []

        # 1. Course Recommendations for Top Gap Domains
        candidate_courses = (
            db.query(Course)
            .filter(~Course.id.in_(completed_course_ids) if completed_course_ids else True)
            .all()
        )

        for gap_comp in gap_competencies[:3]:
            dom_code = gap_comp["domain_code"]
            # Find matching candidate course
            matched_course = next(
                (c for c in candidate_courses if dom_code in c.category.lower() or dom_code in c.title.lower() or any(
                    gap_comp["name"].lower() in (cs.skill.name.lower() if cs.skill else "")
                    for cs in (c.course_skills or [])
                )),
                None
            )
            if not matched_course and candidate_courses:
                matched_course = candidate_courses[0]

            if matched_course and not any(r["item_id"] == matched_course.id and r["type"] == "course" for r in recommendations_output):
                reason = (
                    f"Identified {gap_comp['status'].upper()} in {gap_comp['name']} (Current: {gap_comp['level']:.1f} / Target: {gap_comp['target_level']:.1f}). "
                    f"Completing this {matched_course.difficulty} course directly closes the {gap_comp['gap']:.1f}-level competency gap."
                )
                rec_row = Recommendation(
                    user_id=user_id,
                    course_id=matched_course.id,
                    reason=reason,
                    score=round(gap_comp["gap"] * 20.0, 1),
                    status="pending",
                    generated_at=datetime.datetime.utcnow(),
                )
                db.add(rec_row)
                db.flush()

                recommendations_output.append({
                    "id": rec_row.id,
                    "type": "course",
                    "item_id": matched_course.id,
                    "title": matched_course.title,
                    "category": matched_course.category,
                    "difficulty": matched_course.difficulty,
                    "duration": f"{matched_course.duration_hours:g} hours",
                    "reason": reason,
                    "target_competency": gap_comp["name"],
                    "current_level": gap_comp["level"],
                    "target_level": gap_comp["target_level"],
                    "href": f"/courses/{matched_course.id}",
                    "status": "pending",
                })

        # 2. Hands-on Lab Recommendations for Technical & Cyber Gaps
        tech_or_cyber_gaps = [c for c in gap_competencies if c["domain_code"] in ["technical", "digital_governance"]]
        if tech_or_cyber_gaps:
            top_tech = tech_or_cyber_gaps[0]
            if top_tech["domain_code"] == "technical":
                lab_slug = "python-pandas-transform-001" if "pandas" in top_tech["name"].lower() or "python" in top_tech["name"].lower() else "python-debugging-pfms-001"
                lab_title = "Data Cleaning & Aggregation Pipeline with Pandas" if lab_slug == "python-pandas-transform-001" else "Debugging & Exception Resolution in Data Validation"
                lab_reason = f"Targeted hands-on coding lab to raise {top_tech['name']} mastery from {top_tech['mastery_percent']}% to proficiency."
                recommendations_output.append({
                    "id": 9001,
                    "type": "lab",
                    "item_id": lab_slug,
                    "title": lab_title,
                    "category": "Technical Competency",
                    "difficulty": "intermediate",
                    "duration": "30 mins",
                    "reason": lab_reason,
                    "target_competency": top_tech["name"],
                    "current_level": top_tech["level"],
                    "target_level": top_tech["target_level"],
                    "href": f"/labs/{lab_slug}?courseId=3",
                    "status": "pending",
                })
            else:
                cyber_reason = f"Hands-on defensive sandbox investigation to address {top_tech['name']} gap of {top_tech['gap']:.1f} levels."
                recommendations_output.append({
                    "id": 9002,
                    "type": "cyber_sandbox",
                    "item_id": "flagship_incident_001",
                    "title": "Aadhaar e-KYC API Security & Unauthorized Credential Exfiltration",
                    "category": "Digital Governance",
                    "difficulty": "advanced",
                    "duration": "45 mins",
                    "reason": cyber_reason,
                    "target_competency": top_tech["name"],
                    "current_level": top_tech["level"],
                    "target_level": top_tech["target_level"],
                    "href": "/digital-governance/sandbox?courseId=4",
                    "status": "pending",
                })

        # 3. Practice Quiz / Adaptive Statistical Assessment
        stat_or_behav_gaps = [c for c in gap_competencies if c["domain_code"] in ["statistical", "behavioural"]]
        if stat_or_behav_gaps:
            top_sb = stat_or_behav_gaps[0]
            if top_sb["domain_code"] == "statistical":
                recommendations_output.append({
                    "id": 9003,
                    "type": "adaptive_exam",
                    "item_id": "price_statistics",
                    "title": "Adaptive Price Statistics & Laspeyres Index Assessment",
                    "category": "Statistical Competencies",
                    "difficulty": "intermediate",
                    "duration": "15 mins",
                    "reason": f"Adaptive test engine dynamically calibrates questions to accelerate {top_sb['name']} level toward {top_sb['target_level']:.1f}.",
                    "target_competency": top_sb["name"],
                    "current_level": top_sb["level"],
                    "target_level": top_sb["target_level"],
                    "href": "/statistical/exam?courseId=2",
                    "status": "pending",
                })
            else:
                recommendations_output.append({
                    "id": 9004,
                    "type": "ai_interview",
                    "item_id": "ethics_conduct",
                    "title": "AI Oral Board & Socratic Disciplinary Inquiry",
                    "category": "Behavioural & Managerial",
                    "difficulty": "intermediate",
                    "duration": "20 mins",
                    "reason": f"Live Socratic interview evaluates statutory reasoning under Rule 14 to bridge the {top_sb['gap']:.1f}-level gap in {top_sb['name']}.",
                    "target_competency": top_sb["name"],
                    "current_level": top_sb["level"],
                    "target_level": top_sb["target_level"],
                    "href": "/behavioural/interview?courseId=1",
                    "status": "pending",
                })

        db.commit()
        return recommendations_output
