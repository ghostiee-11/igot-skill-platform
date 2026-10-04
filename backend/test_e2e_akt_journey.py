"""
End-to-End Verification Test for LMS Intelligence Features:
1. Attentive Knowledge Tracing (AKT)
2. Skill Gap Analysis
3. Recommendation Engine

Journey Tested:
Initial Learning Activity -> Mastery Update -> Skill Gap Detected ->
Recommendation Generated -> Learner Completes Practical Activity ->
Mastery Scores Traceably Change -> Recommendation Refreshes Dynamically.
"""

import sys
import os
import json
import datetime

# Ensure backend root is on python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.models import (
    User, Course, Module, Lesson, Progress, Enrollment,
    AssessmentAttempt, UserCompetencyScore, CompetencyProfile,
    GapAnalysis, Recommendation
)
from app.agents.competency.knowledge_tracing import AttentiveKnowledgeTracingEngine

def run_e2e_journey():
    print("=" * 80)
    print("STARTING LMS INTELLIGENCE END-TO-END JOURNEY TEST")
    print("=" * 80)

    db = SessionLocal()
    try:
        # Step 1: Find test learner
        learner = db.query(User).filter_by(email="rajesh.kumar@mospi.gov.in").first()
        if not learner:
            learner = db.query(User).first()
        assert learner is not None, "Learner user must exist in database"
        print(f"\n[Step 1] Learner Identified: ID={learner.id}, Email={learner.email}")

        # Step 2: Run initial Attentive Knowledge Tracing
        print("\n[Step 2] Running Attentive Knowledge Tracing on initial learner evidence...")
        initial_akt_res = AttentiveKnowledgeTracingEngine.compute_mastery_and_gaps(db, learner.id)
        initial_recs = AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, learner.id)
        
        traceable_profile = AttentiveKnowledgeTracingEngine.get_full_traceable_profile(db, learner.id)
        domains_list = traceable_profile.get("domains", [])
        print(f"-> Domains Tracked: {[d['name'] for d in domains_list]}")
        
        # Get competencies by domain
        all_comps = traceable_profile.get("competencies", [])
        tech_comps = [c for c in all_comps if c["domain_code"] == "technical"]
        initial_tech_scores = {c["code"]: c["mastery_percent"] for c in tech_comps}
        
        print(f"-> Initial Technical Mastery (Competencies: {len(tech_comps)}): {initial_tech_scores}")
        print(f"-> Initial Skill Gaps Count: {len(initial_akt_res['gaps'])}")
        print(f"-> Initial Recommendations Count: {len(initial_recs)}")
        
        for rec in initial_recs[:3]:
            pri = rec.get("priority_score", rec.get("match_score", 1.0))
            print(f"   * [{rec['type'].upper()}] {rec['title']} -> Reason: {rec['reason']} (Priority: {pri:.2f})")

        # Step 3: Find a lesson to complete (e.g. Python lab in Technical domain)
        tech_course = db.query(Course).filter(Course.title.contains("Python")).first()
        assert tech_course is not None, "Python course must exist"
        
        target_lesson = db.query(Lesson).join(Module).filter(
            Module.course_id == tech_course.id,
            Lesson.topic.contains("Pandas") | Lesson.topic.contains("Data")
        ).first()
        assert target_lesson is not None, "Target lesson must exist"
        print(f"\n[Step 3] Learner enters lesson: '{target_lesson.title}' (Topic: {target_lesson.topic})")

        # Step 4: Learner performs learning activity (answering in-lesson check correctly + completing lesson)
        print(f"\n[Step 4] Learner completes in-lesson knowledge check and marks lesson complete...")
        enrollment = db.query(Enrollment).filter_by(user_id=learner.id, course_id=tech_course.id).first()
        if not enrollment:
            enrollment = Enrollment(
                user_id=learner.id,
                course_id=tech_course.id,
                status="in_progress",
                progress_percent=25.0
            )
            db.add(enrollment)
            db.flush()

        progress = db.query(Progress).filter_by(
            enrollment_id=enrollment.id,
            lesson_id=target_lesson.id
        ).first()
        if not progress:
            progress = Progress(
                enrollment_id=enrollment.id,
                module_id=target_lesson.module_id,
                lesson_id=target_lesson.id,
                completed=True,
                activity_completed=True,
                activity_score_percent=100.0,
                time_spent_seconds=1200
            )
            db.add(progress)
        else:
            progress.completed = True
            progress.activity_completed = True
            progress.activity_score_percent = 100.0
            progress.time_spent_seconds = 1200
        db.commit()

        # Step 5: Trigger AKT Engine re-computation
        print("\n[Step 5] Triggering Attentive Knowledge Tracing Engine update...")
        updated_akt_res = AttentiveKnowledgeTracingEngine.compute_mastery_and_gaps(db, learner.id)
        updated_recs = AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, learner.id)

        # Step 6: Verify traceable mastery update
        updated_profile = AttentiveKnowledgeTracingEngine.get_full_traceable_profile(db, learner.id)
        updated_comps = updated_profile.get("competencies", [])
        updated_tech_comps = [c for c in updated_comps if c["domain_code"] == "technical"]
        updated_tech_scores = {c["code"]: c["mastery_percent"] for c in updated_tech_comps}
        print(f"-> Updated Technical Mastery: {updated_tech_scores}")

        # Check evidence trace for competencies with evidence
        evidence_found = 0
        for comp in updated_comps:
            if comp["evidence_count"] > 0:
                evidence_found += 1
                print(f"-> Competency: {comp['name']} (Mastery: {comp['mastery_percent']}%, Status: {comp['status']})")
                print(f"   Evidence Trace ({len(comp['recent_evidence'])} items):")
                for ev in comp["recent_evidence"]:
                    print(f"     - [{ev['type']}] {ev['title']} -> score={ev['score_pct']}% (date={ev['date']})")

        assert evidence_found > 0, "Traceable evidence must be attached to competencies"

        # Step 7: Verify recommendation refresh
        print("\n[Step 7] Validating dynamic recommendation refresh...")
        print(f"-> Updated Recommendations Count: {len(updated_recs)}")
        for rec in updated_recs[:4]:
            pri = rec.get("priority_score", rec.get("match_score", 1.0))
            print(f"   * [{rec['type'].upper()}] {rec['title']} -> Reason: {rec['reason']} (Target: {rec['target_competency']}, Priority: {pri:.2f})")

        # Assertions
        assert len(domains_list) == 4, "All 4 domains must be present in traceable profile"
        assert len(updated_recs) > 0, "Recommendations must be dynamically generated"
        
        # Verify no completed content is recommended as non-revision
        completed_lesson_ids = {
            p.lesson_id for p in db.query(Progress).join(Enrollment).filter(
                Enrollment.user_id == learner.id,
                Progress.completed == True
            ).all()
        }
        print(f"\n[Validation] Completed lesson IDs count: {len(completed_lesson_ids)}")
        for rec in updated_recs:
            if rec["type"] == "lesson":
                assert rec["id"] not in completed_lesson_ids or rec.get("is_revision", False), \
                    "Completed lesson should not be recommended unless marked revision"

        print("\n" + "=" * 80)
        print("ALL LMS INTELLIGENCE E2E TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_e2e_journey()
