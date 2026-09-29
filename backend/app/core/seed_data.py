import json
import datetime
from sqlalchemy.orm import Session
from app.models.models import (
    User, UserProfile, Department, Course, Module, Lesson,
    Skill, CourseSkill, UserSkill, Enrollment, Progress,
    Assessment, Question, PlannedCourse, LearningHistory
)
from app.core.security import get_password_hash
from app.modules.digital_governance.seed_data import (
    seed_digital_governance_curriculum,
    seed_cybersec_challenges,
)

from sqlalchemy import text

def ensure_lesson_schema_columns(db: Session):
    """Safely adds segment timestamps and metadata columns to lessons table if they do not exist."""
    columns_to_add = [
        ("video_start_time", "INTEGER DEFAULT 0"),
        ("video_end_time", "INTEGER"),
        ("source_video_title", "VARCHAR(255)"),
        ("topic", "VARCHAR(100)"),
        ("learning_objective", "TEXT"),
    ]
    for col_name, col_type in columns_to_add:
        try:
            db.execute(text(f"ALTER TABLE lessons ADD COLUMN {col_name} {col_type}"))
            db.commit()
        except Exception:
            db.rollback()

def sync_course_curriculum_videos(db: Session):
    """Synchronizes modules and lesson segment-level video metadata across all 4 courses in the database."""
    ensure_lesson_schema_columns(db)

    # 1. Course 1: Behavioural Competency
    c1 = db.query(Course).filter(Course.title == "Civil Service Conduct, Administrative Ethics & Interpersonal Leadership").first()
    if c1:
        # Module 1
        m1_1 = db.query(Module).filter(Module.course_id == c1.id, Module.order == 1).first()
        if not m1_1:
            m1_1 = Module(course_id=c1.id, title="Module 1: Statutory Code of Conduct & Ethics", description="CCS (Conduct) Rules 1964, integrity standards, and avoidance of conflict of interest.", order=1)
            db.add(m1_1)
            db.flush()
        
        l1_1_1 = db.query(Lesson).filter(Lesson.module_id == m1_1.id, Lesson.order == 1).first()
        if not l1_1_1:
            l1_1_1 = Lesson(
                module_id=m1_1.id,
                title="Lesson 1: Statutory Framework of CCS (Conduct) Rules, 1964",
                topic="Statutory Conduct & General Principles of Integrity",
                learning_objective="Analyze Rule 3 obligations, constitutional neutrality, and statutory limitations on administrative discretion.",
                source_video_title="OnlyIAS - Civil Service Ethics & Administrative Conduct Masterclass",
                content_type="video",
                duration_minutes=21,
                video_url="https://www.youtube.com/watch?v=hPGz-XBfVbM",
                video_start_time=0,
                video_end_time=1260,
                content="""# Statutory Framework of CCS (Conduct) Rules, 1964\n\nEvery civil servant in the Government of India is governed by the statutory provisions of the Central Civil Services (Conduct) Rules, 1964.\n\n### Core Tenets:\n- Maintain absolute integrity, devotion to duty, and political neutrality.\n- Uphold supremacy of the Constitution and public trust.""",
                activity_question="Under Rule 3 of the CCS (Conduct) Rules, what is the paramount obligation of an administrative officer?",
                activity_options_json=json.dumps(["To maintain absolute integrity, devotion to duty, and political neutrality", "To obey verbal instructions from non-official acquaintances", "To maximize fee collections arbitrarily", "To bypass statutory tender processes"]),
                activity_correct_option=0,
                activity_explanation="Rule 3(1) mandates absolute integrity, dedication to duty, and conduct worthy of an officer of the State.",
                order=1
            )
            db.add(l1_1_1)
        else:
            l1_1_1.topic = "Statutory Conduct & General Principles of Integrity"
            l1_1_1.learning_objective = "Analyze Rule 3 obligations, constitutional neutrality, and statutory limitations on administrative discretion."
            l1_1_1.source_video_title = "OnlyIAS - Civil Service Ethics & Administrative Conduct Masterclass"
            l1_1_1.video_url = "https://www.youtube.com/watch?v=hPGz-XBfVbM"
            l1_1_1.video_start_time = 0
            l1_1_1.video_end_time = 1260
            l1_1_1.duration_minutes = 21
            l1_1_1.content_type = "video"

        l1_1_2 = db.query(Lesson).filter(Lesson.module_id == m1_1.id, Lesson.order == 2).first()
        if not l1_1_2:
            l1_1_2 = Lesson(
                module_id=m1_1.id,
                title="Lesson 2: Ethical Decision Making & Conflict of Interest",
                topic="Conflict of Interest, Gifts & Pecuniary Bias",
                learning_objective="Master statutory recusal protocols, gifts declaration limits (Rule 13), and commercial cooling-off periods.",
                source_video_title="Drishti IAS - Ethics & Administrative Decision Making",
                content_type="video",
                duration_minutes=22,
                video_url="https://www.youtube.com/watch?v=F7p3z9H1BbM",
                video_start_time=180,
                video_end_time=1500,
                content="""# Ethical Decision Making & Managing Conflicts of Interest\n\nPublic trust relies on the transparent declaration and mitigation of actual, potential, or perceived conflicts of interest.""",
                activity_question="When an official matter involves an entity where a relative holds a financial interest, what is the correct procedural action?",
                activity_options_json=json.dumps(["Formally disclose the relationship in writing and recuse from the decision-making process", "Proceed with the file if no monetary gain is directly transferred", "Keep the information confidential to avoid administrative delays", "Delegate the decision verbally to a junior staff member"]),
                activity_correct_option=0,
                activity_explanation="Administrative ethics require explicit disclosure and formal recusal whenever a conflict of interest arises.",
                order=2
            )
            db.add(l1_1_2)
        else:
            l1_1_2.topic = "Conflict of Interest, Gifts & Pecuniary Bias"
            l1_1_2.learning_objective = "Master statutory recusal protocols, gifts declaration limits (Rule 13), and commercial cooling-off periods."
            l1_1_2.source_video_title = "Drishti IAS - Ethics & Administrative Decision Making"
            l1_1_2.video_url = "https://www.youtube.com/watch?v=F7p3z9H1BbM"
            l1_1_2.video_start_time = 180
            l1_1_2.video_end_time = 1500
            l1_1_2.duration_minutes = 22
            l1_1_2.content_type = "video"

        # Module 2
        m1_2 = db.query(Module).filter(Module.course_id == c1.id, Module.order == 2).first()
        if not m1_2:
            m1_2 = Module(course_id=c1.id, title="Module 2: Quasi-Judicial Inquiries & Natural Justice", description="Conducting departmental proceedings under Rule 14 CCS (CCA) Rules.", order=2)
            db.add(m1_2)
            db.flush()

        l1_2_1 = db.query(Lesson).filter(Lesson.module_id == m1_2.id, Lesson.order == 1).first() or db.query(Lesson).filter(Lesson.module_id == m1_2.id).first()
        if not l1_2_1:
            l1_2_1 = Lesson(
                module_id=m1_2.id,
                title="Lesson 3: Principles of Natural Justice (Audi Alteram Partem)",
                topic="Quasi-Judicial Inquiries & Evidence Disclosure",
                learning_objective="Execute Rule 14 departmental inquiry steps ensuring fair notice, document inspection, and cross-examination rights.",
                source_video_title="Prof. Jeffrey Kaplan - Moral & Legal Obligations of Fair Hearing",
                content_type="video",
                duration_minutes=20,
                video_url="https://www.youtube.com/watch?v=DLCUn6h7qRo",
                video_start_time=60,
                video_end_time=1260,
                content="""# Audi Alteram Partem in Departmental Proceedings\n\nIn any quasi-judicial proceeding governed by Rule 14 of CCS (CCA) Rules, 1965, the Charged Officer must be given fair notice and opportunity to inspect evidence.""",
                activity_question="What does the doctrine of Audi Alteram Partem require during a Rule 14 inquiry?",
                activity_options_json=json.dumps(["Granting fair hearing and opportunity to inspect evidence and cross-examine witnesses", "Allowing the prosecution to hide confidential witness statements", "Ordering immediate punishment without recording evidence", "Conducting ex-parte hearings without notice"]),
                activity_correct_option=0,
                activity_explanation="Audi Alteram Partem guarantees no person shall be condemned unheard.",
                order=1
            )
            db.add(l1_2_1)
        else:
            l1_2_1.title = "Lesson 3: Principles of Natural Justice (Audi Alteram Partem)"
            l1_2_1.topic = "Quasi-Judicial Inquiries & Evidence Disclosure"
            l1_2_1.learning_objective = "Execute Rule 14 departmental inquiry steps ensuring fair notice, document inspection, and cross-examination rights."
            l1_2_1.source_video_title = "Prof. Jeffrey Kaplan - Moral & Legal Obligations of Fair Hearing"
            l1_2_1.video_url = "https://www.youtube.com/watch?v=DLCUn6h7qRo"
            l1_2_1.video_start_time = 60
            l1_2_1.video_end_time = 1260
            l1_2_1.duration_minutes = 20
            l1_2_1.content_type = "video"
            l1_2_1.order = 1

        # Module 3
        m1_3 = db.query(Module).filter(Module.course_id == c1.id, Module.order == 3).first()
        if not m1_3:
            m1_3 = Module(course_id=c1.id, title="Module 3: Administrative Negotiation & Public Leadership", description="High-pressure public communication, grievance redressal, and crisis leadership.", order=3)
            db.add(m1_3)
            db.flush()

        l1_3_1 = db.query(Lesson).filter(Lesson.module_id == m1_3.id, Lesson.order == 1).first()
        if not l1_3_1:
            l1_3_1 = Lesson(
                module_id=m1_3.id,
                title="Lesson 4: Public Grievance Redressal & Crisis Negotiation",
                topic="Crisis De-escalation & CPGRAMS Redressal",
                learning_objective="Deploy strategic communication frameworks to resolve public grievances and issue reasoned speaking orders.",
                source_video_title="Stanford Graduate School of Business - Communication & Negotiation in High Stakes",
                content_type="video",
                duration_minutes=20,
                video_url="https://www.youtube.com/watch?v=HAnw168huqA",
                video_start_time=120,
                video_end_time=1320,
                content="""# Public Grievance Redressal & Crisis Stakeholder Negotiation\n\nCivil servants frequently navigate high-stakes community grievances, public protests, and emergency stakeholder meetings.""",
                activity_question="Under standard administrative guidelines, how should a citizen grievance on CPGRAMS be concluded?",
                activity_options_json=json.dumps(["With a reasoned speaking order explaining the statutory grounds and redressal action taken", "With a generic one-line closure note without inspection", "By forwarding the grievance indefinitely between departments", "By closing the ticket after 48 hours automatically"]),
                activity_correct_option=0,
                activity_explanation="Grievance disposal requires a reasoned speaking order transparently outlining the statutory resolution.",
                order=1
            )
            db.add(l1_3_1)
        else:
            l1_3_1.topic = "Crisis De-escalation & CPGRAMS Redressal"
            l1_3_1.learning_objective = "Deploy strategic communication frameworks to resolve public grievances and issue reasoned speaking orders."
            l1_3_1.source_video_title = "Stanford Graduate School of Business - Communication & Negotiation in High Stakes"
            l1_3_1.video_url = "https://www.youtube.com/watch?v=HAnw168huqA"
            l1_3_1.video_start_time = 120
            l1_3_1.video_end_time = 1320
            l1_3_1.duration_minutes = 20
            l1_3_1.content_type = "video"

    # 2. Course 2: Statistical Competency
    c2 = db.query(Course).filter(Course.title == "Compilation of Consumer Price Index (CPI) & Inflation Metrics").first()
    if c2:
        # Module 1
        m2_1 = db.query(Module).filter(Module.course_id == c2.id, Module.order == 1).first()
        if not m2_1:
            m2_1 = Module(course_id=c2.id, title="Module 1: Index Formulation & Basket Selection", description="Mathematical foundations of modified Laspeyres and Jevons price relatives.", order=1)
            db.add(m2_1)
            db.flush()

        l2_1_1 = db.query(Lesson).filter(Lesson.module_id == m2_1.id, Lesson.order == 1).first()
        if not l2_1_1:
            l2_1_1 = Lesson(
                module_id=m2_1.id,
                title="Lesson 1: The Modified Laspeyres Price Index Formula",
                topic="Modified Laspeyres Price Formulation",
                learning_objective="Derive the Modified Laspeyres price index formula and normalize consumption expenditure survey (CES) weights.",
                source_video_title="Quantitative Index Formulation & Laspeyres Mathematics",
                content_type="video",
                duration_minutes=23,
                video_url="https://www.youtube.com/watch?v=L2OochgcO3E",
                video_start_time=300,
                video_end_time=1680,
                content="""# The Modified Laspeyres Formula in CPI Compilation\n\nIn India's official CPI (Base 2012=100), elementary price indices are aggregated using a Modified Laspeyres Formula with Jevons geometric mean at quotation level.""",
                activity_question="Which index formula is employed at the elementary quotation level to minimize substitution bias?",
                activity_options_json=json.dumps(["Geometric Mean (Jevons Index)", "Simple Harmonic Mean", "Carli Arithmetic Index", "Dutot Ratio of Averages"]),
                activity_correct_option=0,
                activity_explanation="MoSPI guidelines use the Geometric Mean (Jevons) at the elementary quotation level.",
                order=1
            )
            db.add(l2_1_1)
        else:
            l2_1_1.topic = "Modified Laspeyres Price Formulation"
            l2_1_1.learning_objective = "Derive the Modified Laspeyres price index formula and normalize consumption expenditure survey (CES) weights."
            l2_1_1.source_video_title = "Quantitative Index Formulation & Laspeyres Mathematics"
            l2_1_1.video_url = "https://www.youtube.com/watch?v=L2OochgcO3E"
            l2_1_1.video_start_time = 300
            l2_1_1.video_end_time = 1680
            l2_1_1.duration_minutes = 23
            l2_1_1.content_type = "video"

        l2_1_2 = db.query(Lesson).filter(Lesson.module_id == m2_1.id, Lesson.order == 2).first()
        if not l2_1_2:
            l2_1_2 = Lesson(
                module_id=m2_1.id,
                title="Lesson 2: Elementary Price Relatives & Weight Aggregation",
                topic="Jevons Geometric Mean & Price Relatives",
                learning_objective="Calculate elementary price relatives at the quotation level with Jevons geometric mean to minimize substitution bias.",
                source_video_title="Price Lesson - Elementary Price Quotation Aggregation",
                content_type="video",
                duration_minutes=22,
                video_url="https://www.youtube.com/watch?v=KwS0XZb4qGA",
                video_start_time=180,
                video_end_time=1500,
                content="""# Elementary Price Relatives & Weight Aggregation\n\nPrice relatives represent the ratio of current price to base price: R_i = (P_t / P_0) * 100.""",
                activity_question="If an item with base price Rs. 80 is sold at Rs. 100 in period t, what is its elementary price relative?",
                activity_options_json=json.dumps(["125.0", "80.0", "120.0", "105.0"]),
                activity_correct_option=0,
                activity_explanation="Price Relative = (100 / 80) * 100 = 125.0",
                order=2
            )
            db.add(l2_1_2)
        else:
            l2_1_2.topic = "Jevons Geometric Mean & Price Relatives"
            l2_1_2.learning_objective = "Calculate elementary price relatives at the quotation level with Jevons geometric mean to minimize substitution bias."
            l2_1_2.source_video_title = "Price Lesson - Elementary Price Quotation Aggregation"
            l2_1_2.video_url = "https://www.youtube.com/watch?v=KwS0XZb4qGA"
            l2_1_2.video_start_time = 180
            l2_1_2.video_end_time = 1500
            l2_1_2.duration_minutes = 22
            l2_1_2.content_type = "video"

        # Module 2
        m2_2 = db.query(Module).filter(Module.course_id == c2.id, Module.order == 2).first()
        if not m2_2:
            m2_2 = Module(course_id=c2.id, title="Module 2: Imputation & Quality Adjustment", description="Techniques for disappearing items, seasonal goods, and rent imputation.", order=2)
            db.add(m2_2)
            db.flush()

        l2_2_1 = db.query(Lesson).filter(Lesson.module_id == m2_2.id, Lesson.order == 1).first()
        if not l2_2_1:
            l2_2_1 = Lesson(
                module_id=m2_2.id,
                title="Lesson 3: Handling Disappearing Quotations & House Rent Imputation",
                topic="Class Mean Imputation & Rent Quality Adjustment",
                learning_objective="Apply class-mean imputation algorithms for temporarily unavailable items and semi-annual repeat rent surveys.",
                source_video_title="Modelware Systems - Data Quality Frameworks & Imputation",
                content_type="video",
                duration_minutes=20,
                video_url="https://www.youtube.com/watch?v=RuNp3l_2dGs",
                video_start_time=240,
                video_end_time=1440,
                content="""# Imputation Techniques for Missing Price Quotations\n\nTechniques for handling missing price quotations: Class mean imputation, chain relatives, and repeat rent surveys.""",
                activity_question="When a specific vegetable variety is temporarily unavailable in a market, which imputation method is standard?",
                activity_options_json=json.dumps(["Imputing the price trend from the available varieties in the same sub-group", "Setting the price to zero", "Using the highest price recorded across all states", "Deleting the entire commodity from the state basket"]),
                activity_correct_option=0,
                activity_explanation="Class mean imputation uses the subgroup price trend to estimate missing quotations accurately.",
                order=1
            )
            db.add(l2_2_1)
        else:
            l2_2_1.topic = "Class Mean Imputation & Rent Quality Adjustment"
            l2_2_1.learning_objective = "Apply class-mean imputation algorithms for temporarily unavailable items and semi-annual repeat rent surveys."
            l2_2_1.source_video_title = "Modelware Systems - Data Quality Frameworks & Imputation"
            l2_2_1.video_url = "https://www.youtube.com/watch?v=RuNp3l_2dGs"
            l2_2_1.video_start_time = 240
            l2_2_1.video_end_time = 1440
            l2_2_1.duration_minutes = 20
            l2_2_1.content_type = "video"

    # 3. Course 3: Technical Competency (Restructured into Module 1: Comprehensive Masterclass & Module 2: Practice & Labs)
    c3 = db.query(Course).filter(Course.title == "Python and Data Cleaning Pipelines for Public Policy").first()
    if c3:
        # Clean up any legacy Module 3 if present
        legacy_m3 = db.query(Module).filter(Module.course_id == c3.id, Module.order > 2).all()
        for lm in legacy_m3:
            for ll in lm.lessons:
                db.delete(ll)
            db.delete(lm)
        db.flush()

        # Module 1: Masterclass & Foundations
        m3_1 = db.query(Module).filter(Module.course_id == c3.id, Module.order == 1).first()
        if not m3_1:
            m3_1 = Module(
                course_id=c3.id,
                title="Module 1: Comprehensive Python & Data Wrangling Masterclass",
                description="Complete masterclass video lecture covering Python microdata data structures, vectorized Pandas operations, missing value imputation, and Pydantic validation.",
                order=1
            )
            db.add(m3_1)
            db.flush()
        else:
            m3_1.title = "Module 1: Comprehensive Python & Data Wrangling Masterclass"
            m3_1.description = "Complete masterclass video lecture covering Python microdata data structures, vectorized Pandas operations, missing value imputation, and Pydantic validation."

        # Module 1 - Lesson 1
        l3_1_1 = db.query(Lesson).filter(Lesson.module_id == m3_1.id, Lesson.order == 1).first()
        if not l3_1_1:
            l3_1_1 = Lesson(
                module_id=m3_1.id,
                title="Lesson 1: Python Fundamentals & Data Handling for Policy Analysts",
                topic="Python Data Structures & Policy Microdata",
                learning_objective="Master Python core data structures, memory layouts, and dictionary-based record processing for public policy datasets.",
                source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
                content_type="video",
                duration_minutes=40,
                video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
                video_start_time=0,
                video_end_time=2400,
                content="""# Python Fundamentals & Microdata Structures\n\nWhen processing administrative returns and household survey data, selecting optimal in-memory data structures prevents memory blowups and slow iteration times.""",
                activity_question="Which Python data structure provides O(1) average-time lookups by unique identifier?",
                activity_options_json=json.dumps(["Dictionary (dict / hash map)", "Unsorted List", "Nested Tuple", "Linked File Buffer"]),
                activity_correct_option=0,
                activity_explanation="Python dictionaries utilize hash tables offering O(1) average lookup time.",
                order=1
            )
            db.add(l3_1_1)
        else:
            l3_1_1.title = "Lesson 1: Python Fundamentals & Data Handling for Policy Analysts"
            l3_1_1.topic = "Python Data Structures & Policy Microdata"
            l3_1_1.learning_objective = "Master Python core data structures, memory layouts, and dictionary-based record processing for public policy datasets."
            l3_1_1.source_video_title = "CodeWithHarry - Python Programming & Data Structures Masterclass"
            l3_1_1.video_url = "https://www.youtube.com/watch?v=UrsmFxEIp5k"
            l3_1_1.video_start_time = 0
            l3_1_1.video_end_time = 2400
            l3_1_1.duration_minutes = 40
            l3_1_1.content_type = "video"

        # Module 1 - Lesson 2
        l3_1_2 = db.query(Lesson).filter(Lesson.module_id == m3_1.id, Lesson.order == 2).first()
        if not l3_1_2:
            l3_1_2 = Lesson(
                module_id=m3_1.id,
                title="Lesson 2: Vectorized Data Wrangling with Pandas",
                topic="Pandas Vectorization vs Iterative Loops",
                learning_objective="Implement vectorized series operations and Boolean masking on administrative tables without slow Python interpreter loops.",
                source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
                content_type="video",
                duration_minutes=45,
                video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
                video_start_time=2400,
                video_end_time=5400,
                content="""# Vectorized Data Wrangling with Pandas\n\nWhen processing large-scale public policy microdata, vectorized Pandas calculations delegate execution to compiled NumPy C routines, yielding massive performance speedups over iterative loops.""",
                activity_question="Why should vectorized methods be preferred over row-by-row for-loops in Pandas?",
                activity_options_json=json.dumps(["Vectorized calculations run in compiled C routines and are orders of magnitude faster", "Because for-loops are deprecated in Python 3.12", "Because vectorized methods use less hard disk space", "Because Pandas does not support for-loops"]),
                activity_correct_option=0,
                activity_explanation="Pandas vectorization delegates calculations to compiled NumPy C routines without Python interpreter loop overhead.",
                order=2
            )
            db.add(l3_1_2)
        else:
            l3_1_2.title = "Lesson 2: Vectorized Data Wrangling with Pandas"
            l3_1_2.topic = "Pandas Vectorization vs Iterative Loops"
            l3_1_2.learning_objective = "Implement vectorized series operations and Boolean masking on administrative tables without slow Python interpreter loops."
            l3_1_2.source_video_title = "CodeWithHarry - Python Programming & Data Structures Masterclass"
            l3_1_2.video_url = "https://www.youtube.com/watch?v=UrsmFxEIp5k"
            l3_1_2.video_start_time = 2400
            l3_1_2.video_end_time = 5400
            l3_1_2.duration_minutes = 45
            l3_1_2.content_type = "video"

        # Module 1 - Lesson 3
        l3_1_3 = db.query(Lesson).filter(Lesson.module_id == m3_1.id, Lesson.order == 3).first()
        if not l3_1_3:
            l3_1_3 = Lesson(
                module_id=m3_1.id,
                title="Lesson 3: Missing Value Treatment, Outlier Detection & Multiplier Scaling",
                topic="Missing Value Imputation & Survey Multipliers",
                learning_objective="Sanitize survey missing sentinel codes, scale sampling weights, and calculate weighted population statistics.",
                source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
                content_type="video",
                duration_minutes=40,
                video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
                video_start_time=5400,
                video_end_time=8400,
                content="""# Cleaning Missing Values and Applying Sampling Multipliers\n\nIn NSSO and PLFS microdata, missing codes must be converted to NaN and weights scaled appropriately.""",
                activity_question="How should survey sentinel missing values (such as 999999) be handled before statistical calculation?",
                activity_options_json=json.dumps(["Replaced with NaN and handled via explicit masking or domain-approved imputation", "Included directly in standard sum and average calculations", "Replaced with zero without documenting the change", "Ignored by multiplying all rows by 0"]),
                activity_correct_option=0,
                activity_explanation="Sentinel codes must be converted to NaN to prevent distortions in statistical aggregations.",
                order=3
            )
            db.add(l3_1_3)
        else:
            l3_1_3.title = "Lesson 3: Missing Value Treatment, Outlier Detection & Multiplier Scaling"
            l3_1_3.topic = "Missing Value Imputation & Survey Multipliers"
            l3_1_3.learning_objective = "Sanitize survey missing sentinel codes, scale sampling weights, and calculate weighted population statistics."
            l3_1_3.source_video_title = "CodeWithHarry - Python Programming & Data Structures Masterclass"
            l3_1_3.video_url = "https://www.youtube.com/watch?v=UrsmFxEIp5k"
            l3_1_3.video_start_time = 5400
            l3_1_3.video_end_time = 8400
            l3_1_3.duration_minutes = 40
            l3_1_3.content_type = "video"

        # Module 1 - Lesson 4
        l3_1_4 = db.query(Lesson).filter(Lesson.module_id == m3_1.id, Lesson.order == 4).first()
        if not l3_1_4:
            l3_1_4 = Lesson(
                module_id=m3_1.id,
                title="Lesson 4: Administrative Schema Validation with Pydantic & Regex",
                topic="Pydantic Schema Validation & Regex Parsing",
                learning_objective="Validate administrative data against typed Pydantic models with custom field validators and regular expressions.",
                source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
                content_type="video",
                duration_minutes=40,
                video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
                video_start_time=8400,
                video_end_time=11400,
                content="""# Schema Validation & Regex for Administrative Returns\n\nValidating government datasets with Pydantic schemas and regex pattern validators prevents schema drift and invalid data entry.""",
                activity_question="What is the primary advantage of validating data with Pydantic schemas before running analytics?",
                activity_options_json=json.dumps(["Catches schema drift, invalid values, and bad types before corrupt data enters downstream pipelines", "Eliminates the need to ever back up the database", "Converts all data to binary files automatically", "Bypasses database constraints completely"]),
                activity_correct_option=0,
                activity_explanation="Pydantic guarantees strict runtime type and constraint enforcement.",
                order=4
            )
            db.add(l3_1_4)
        else:
            l3_1_4.title = "Lesson 4: Administrative Schema Validation with Pydantic & Regex"
            l3_1_4.topic = "Pydantic Schema Validation & Regex Parsing"
            l3_1_4.learning_objective = "Validate administrative data against typed Pydantic models with custom field validators and regular expressions."
            l3_1_4.source_video_title = "CodeWithHarry - Python Programming & Data Structures Masterclass"
            l3_1_4.video_url = "https://www.youtube.com/watch?v=UrsmFxEIp5k"
            l3_1_4.video_start_time = 8400
            l3_1_4.video_end_time = 11400
            l3_1_4.duration_minutes = 40
            l3_1_4.content_type = "video"

        # Module 2: Practice, Hands-on Labs & Assessment
        m3_2 = db.query(Module).filter(Module.course_id == c3.id, Module.order == 2).first()
        if not m3_2:
            m3_2 = Module(
                course_id=c3.id,
                title="Module 2: Hands-on Practice, Coding Labs & Assessment",
                description="Interactive Jupyter coding workspaces, automated Pytest assertions, data-wrangling challenges, and final certification exam.",
                order=2
            )
            db.add(m3_2)
            db.flush()
        else:
            m3_2.title = "Module 2: Hands-on Practice, Coding Labs & Assessment"
            m3_2.description = "Interactive Jupyter coding workspaces, automated Pytest assertions, data-wrangling challenges, and final certification exam."

        # Module 2 - Lesson 1: Conceptual Quiz
        l3_2_1 = db.query(Lesson).filter(Lesson.module_id == m3_2.id, Lesson.order == 1).first()
        if not l3_2_1:
            l3_2_1 = Lesson(
                module_id=m3_2.id,
                title="Lesson 1: Python & Pandas Knowledge Check (Quiz)",
                topic="Python & Pandas Conceptual Assessment",
                learning_objective="Test conceptual mastery of vectorized computations, memory optimization, and data structures.",
                source_video_title=None,
                content_type="reading",
                duration_minutes=15,
                video_url=None,
                video_start_time=None,
                video_end_time=None,
                content="""# Python & Pandas Conceptual Knowledge Check\n\nReview your theoretical and syntactic mastery before entering the live coding lab workspace.""",
                activity_question="Why do vectorized Pandas calculations vastly outperform Python for-loops on large survey microdata?",
                activity_options_json=json.dumps(["Vectorized operations delegate execution to compiled NumPy C routines without Python interpreter overhead", "Because Python for-loops are not allowed in data science", "Because vectorized operations convert data to text files", "Because loops consume more internet bandwidth"]),
                activity_correct_option=0,
                activity_explanation="Pandas vectorization delegates calculations directly to compiled C code without GIL and loop overhead.",
                order=1
            )
            db.add(l3_2_1)
        else:
            l3_2_1.title = "Lesson 1: Python & Pandas Knowledge Check (Quiz)"
            l3_2_1.topic = "Python & Pandas Conceptual Assessment"
            l3_2_1.learning_objective = "Test conceptual mastery of vectorized computations, memory optimization, and data structures."
            l3_2_1.source_video_title = None
            l3_2_1.video_url = None
            l3_2_1.video_start_time = None
            l3_2_1.video_end_time = None
            l3_2_1.duration_minutes = 15
            l3_2_1.content_type = "reading"

        # Module 2 - Lesson 2: Hands-on Lab 1
        l3_2_2 = db.query(Lesson).filter(Lesson.module_id == m3_2.id, Lesson.order == 2).first()
        if not l3_2_2:
            l3_2_2 = Lesson(
                module_id=m3_2.id,
                title="Lesson 2: Hands-on Lab: Survey Multiplier Scaling & Weight Imputation",
                topic="Pandas Data Cleaning & Aggregation Pipeline",
                learning_objective="Write and execute an end-to-end Pandas data cleaning pipeline calculating weighted population mean income in the interactive sandbox.",
                source_video_title=None,
                content_type="lab",
                duration_minutes=30,
                video_url=None,
                video_start_time=None,
                video_end_time=None,
                content="""# Hands-on Lab: Survey Multiplier Scaling & Weight Imputation\n\nIn this executable lab, you will load a survey dataset, sanitize `-1` and `999999` sentinel missing codes, scale the multiplier weights, and calculate weighted population income metrics.\n\n```python\nimport pandas as pd\nimport numpy as np\n\ndef clean_survey_data(df: pd.DataFrame) -> pd.DataFrame:\n    # 1. Convert missing sentinels to NaN\n    df['income'] = df['income'].replace([999999, -1], np.nan)\n    # 2. Scale multiplier weight\n    df['multiplier_scaled'] = df['multiplier'] / 100.0\n    return df\n```\n\nLaunch the lab workspace below to run and test your implementation with live Pytest assertions.""",
                activity_question="In PLFS survey microdata, what is the role of the multiplier field?",
                activity_options_json=json.dumps(["It represents the inverse probability weight to project sample observations to the total population", "It multiplies the execution speed of the CPU", "It acts as a random encryption salt", "It has no statistical meaning"]),
                activity_correct_option=0,
                activity_explanation="Sampling multipliers are expansion weights that inflate sample records to population estimates.",
                order=2
            )
            db.add(l3_2_2)
        else:
            l3_2_2.title = "Lesson 2: Hands-on Lab: Survey Multiplier Scaling & Weight Imputation"
            l3_2_2.topic = "Pandas Data Cleaning & Aggregation Pipeline"
            l3_2_2.learning_objective = "Write and execute an end-to-end Pandas data cleaning pipeline calculating weighted population mean income in the interactive sandbox."
            l3_2_2.source_video_title = None
            l3_2_2.video_url = None
            l3_2_2.video_start_time = None
            l3_2_2.video_end_time = None
            l3_2_2.duration_minutes = 30
            l3_2_2.content_type = "lab"

        # Module 2 - Lesson 3: Hands-on Lab 2
        l3_2_3 = db.query(Lesson).filter(Lesson.module_id == m3_2.id, Lesson.order == 3).first()
        if not l3_2_3:
            l3_2_3 = Lesson(
                module_id=m3_2.id,
                title="Lesson 3: Hands-on Lab: Administrative Schema Validation with Pydantic",
                topic="Pydantic Schema Validation & Exception Handling",
                learning_objective="Implement and execute Pydantic model validators and regular expression checks on district records in the interactive sandbox.",
                source_video_title=None,
                content_type="lab",
                duration_minutes=30,
                video_url=None,
                video_start_time=None,
                video_end_time=None,
                content="""# Hands-on Lab: Administrative Schema Validation\n\nImplement runtime type and constraint enforcement for government district returns using Pydantic.\n\n```python\nfrom pydantic import BaseModel, Field, field_validator\nimport re\n\nclass DistrictRecord(BaseModel):\n    state_code: int = Field(ge=1, le=38)\n    beneficiary_id: str\n    amount_disbursed: float = Field(ge=0)\n\n    @field_validator('beneficiary_id')\n    @classmethod\n    def check_id_format(cls, v: str) -> str:\n        if not re.match(r'^[A-Z]{2}\\d{8}$', v):\n            raise ValueError('Beneficiary ID must be 2 uppercase letters followed by 8 digits')\n        return v\n```\n\nLaunch the lab workspace below to run and test your schema with live test cases.""",
                activity_question="Which Pydantic decorator allows custom validation logic on specific attributes?",
                activity_options_json=json.dumps(["@field_validator", "@check_column", "@assert_valid", "@db_column"]),
                activity_correct_option=0,
                activity_explanation="Pydantic V2 uses the @field_validator decorator for custom validation functions.",
                order=3
            )
            db.add(l3_2_3)
        else:
            l3_2_3.title = "Lesson 3: Hands-on Lab: Administrative Schema Validation with Pydantic"
            l3_2_3.topic = "Pydantic Schema Validation & Exception Handling"
            l3_2_3.learning_objective = "Implement and execute Pydantic model validators and regular expression checks on district records in the interactive sandbox."
            l3_2_3.source_video_title = None
            l3_2_3.video_url = None
            l3_2_3.video_start_time = None
            l3_2_3.video_end_time = None
            l3_2_3.duration_minutes = 30
            l3_2_3.content_type = "lab"

        # Module 2 - Lesson 4: Hands-on Lab 3
        l3_2_4 = db.query(Lesson).filter(Lesson.module_id == m3_2.id, Lesson.order == 4).first()
        if not l3_2_4:
            l3_2_4 = Lesson(
                module_id=m3_2.id,
                title="Lesson 4: Hands-on Lab: Policy Visualizations & Statistical Summaries",
                topic="Matplotlib & Seaborn Policy Dashboards",
                learning_objective="Generate automated policy distribution plots and quartile binning charts for administrative reporting in the interactive sandbox.",
                source_video_title=None,
                content_type="lab",
                duration_minutes=30,
                video_url=None,
                video_start_time=None,
                video_end_time=None,
                content="""# Hands-on Lab: Policy Visualizations\n\nGenerate standardized distribution plots, box plots, and summary metrics for district welfare allocations.\n\n```python\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport pandas as pd\n\ndef plot_welfare_distribution(df: pd.DataFrame):\n    fig, ax = plt.subplots(figsize=(10, 6))\n    sns.boxplot(x='district_name', y='disbursed_amount', data=df, ax=ax)\n    ax.set_title('Welfare Disbursement Distribution across Districts')\n    return fig\n```\n\nLaunch the lab workspace below to execute and verify your chart generation code.""",
                activity_question="Which chart is standard for identifying interquartile ranges and outlier values across districts?",
                activity_options_json=json.dumps(["Box and Whisker Plot (Boxplot)", "Simple Pie Chart", "Radial Gauge", "Network Flow Graph"]),
                activity_correct_option=0,
                activity_explanation="Box plots show quartiles, median line, and individual outlier markers distinctly.",
                order=4
            )
            db.add(l3_2_4)
        else:
            l3_2_4.title = "Lesson 4: Hands-on Lab: Policy Visualizations & Statistical Summaries"
            l3_2_4.topic = "Matplotlib & Seaborn Policy Dashboards"
            l3_2_4.learning_objective = "Generate automated policy distribution plots and quartile binning charts for administrative reporting in the interactive sandbox."
            l3_2_4.source_video_title = None
            l3_2_4.video_url = None
            l3_2_4.video_start_time = None
            l3_2_4.video_end_time = None
            l3_2_4.duration_minutes = 30
            l3_2_4.content_type = "lab"

    # 4. Course 4: Digital Governance
    c4 = db.query(Course).filter(Course.title == "Digital Governance, Cyber Defense & Public Digital Architecture").first()
    if c4:
        dg_video_map = {
            "Lesson 1: Statutory Mandate of CERT-In & Mandatory 6-Hour Reporting": {
                "url": "https://www.youtube.com/watch?v=3Hpd_1O5F9o",
                "start": 120,
                "end": 1440,
                "duration": 22,
                "topic": "CERT-In Statutory Directives & 6-Hour Reporting",
                "objective": "Comply with Section 70B(6) mandatory 6-hour reporting directives and 180-day log preservation mandates.",
                "source": "Akber Shaikh - National Cyber Security Directives & Compliance"
            },
            "Lesson 2: SOC Authentication Telemetry & Incident Triage": {
                "url": "https://www.youtube.com/watch?v=v3iUx2SNspY",
                "start": 1800,
                "end": 3300,
                "duration": 25,
                "topic": "SOC Telemetry & Threat Containment",
                "objective": "Triage Windows Event 4625/4624 telemetry, isolate infected hosts, and preserve volatile memory under Section 65B.",
                "source": "WsCube Tech - SOC Telemetry Ingestion & Threat Containment"
            },
            "Lesson 1: Obligations of Data Fiduciaries & Significant Data Fiduciaries": {
                "url": "https://www.youtube.com/watch?v=76fcelayw00",
                "start": 240,
                "end": 1680,
                "duration": 24,
                "topic": "DPDP Data Fiduciaries & Penalty Schedules",
                "objective": "Identify legal duties of government Data Fiduciaries and Significant Data Fiduciary compliance requirements.",
                "source": "Prabh Nair - Data Privacy Legal Frameworks & Governance"
            },
            "Lesson 2: Consent Standards, Notice & Citizens' Rights": {
                "url": "https://www.youtube.com/watch?v=wLlQMNbH7wk",
                "start": 60,
                "end": 1260,
                "duration": 20,
                "topic": "Consent Standards & Citizen Data Principal Rights",
                "objective": "Draft valid multilingual pre-consent notices and uphold citizens' rights to access, correction, and erasure.",
                "source": "Data Privacy - Citizen Consent Architectures & Privacy Rights"
            },
            "Lesson 1: Cryptographic Foundations of Class 3 DSC & PKI Hierarchy": {
                "url": "https://www.youtube.com/watch?v=yUeI4nqvNs8",
                "start": 0,
                "end": 900,
                "duration": 15,
                "topic": "Root CA of India & Class 3 DSC Hardware Tokens",
                "objective": "Understand RCAI hierarchy, FIPS 140-2 Level 2 cryptographic hardware tokens, and asymmetric key pairs.",
                "source": "5 Minutes Engineering - Digital Signatures & PKI Cryptography"
            },
            "Lesson 2: e-Office Implementation & Non-Repudiation under Section 65B": {
                "url": "https://www.youtube.com/watch?v=jbBe4AS5pk0",
                "start": 300,
                "end": 1800,
                "duration": 25,
                "topic": "e-Office DSC/eSign & Section 65B Admissibility",
                "objective": "Enforce non-repudiation in electronic secretariat notes and issue Section 65B electronic evidence certificates.",
                "source": "Prof. Christof Paar - Applied Cryptography & Non-Repudiation"
            },
            "Lesson 1: The MeghRaj Architecture & MeitY Empanelment Standards": {
                "url": "https://www.youtube.com/watch?v=BH7SdE0nX5k",
                "start": 0,
                "end": 960,
                "duration": 16,
                "topic": "MeghRaj GI Cloud Architecture & STQC Audits",
                "objective": "Evaluate National Cloud and empaneled commercial cloud service providers against MeitY STQC audit standards.",
                "source": "Learning Shots - GI Cloud MeghRaj Sovereign Architecture"
            },
            "Lesson 2: Sovereign Data Localization, Tenant Isolation & Audits": {
                "url": "https://www.youtube.com/watch?v=70oYrSnRgoI",
                "start": 600,
                "end": 1980,
                "duration": 23,
                "topic": "Sovereign Data Localization & Virtual Isolation",
                "objective": "Architect zero co-location Government Community Clouds with HSM customer-managed encryption.",
                "source": "Apna College - Cloud Architecture, Isolation & Security"
            },
            "Lesson 1: Foundational DPI: Aadhaar Authentication & DigiLocker Gateways": {
                "url": "https://www.youtube.com/watch?v=YyXAxDD4wuQ",
                "start": 180,
                "end": 1500,
                "duration": 22,
                "topic": "Identity & Document Layer: Aadhaar & DigiLocker",
                "objective": "Integrate Aadhaar e-KYC authentication and DigiLocker URI document pushing under Rule 9A.",
                "source": "Vision IAS - Digital Public Infrastructure & India Stack"
            },
            "Lesson 2: Public Financial Management (PFMS DBT) & API Setu Interoperability": {
                "url": "https://www.youtube.com/watch?v=aL5vxyHzr1w",
                "start": 120,
                "end": 1380,
                "duration": 21,
                "topic": "Payments & Open Data Exchange: PFMS TSA & API Setu",
                "objective": "Execute direct benefit transfers via PFMS Treasury Single Account and integrate API Setu standardized endpoints.",
                "source": "ForumIAS - India's DPI Revolution & Direct Benefit Transfer"
            },
        }
        for l in db.query(Lesson).join(Module).filter(Module.course_id == c4.id).all():
            if l.title in dg_video_map:
                meta = dg_video_map[l.title]
                l.video_url = meta["url"]
                l.video_start_time = meta["start"]
                l.video_end_time = meta["end"]
                l.duration_minutes = meta["duration"]
                l.topic = meta["topic"]
                l.learning_objective = meta["objective"]
                l.source_video_title = meta["source"]
                l.content_type = "video"

    db.commit()

def seed_database(db: Session):
    from app.core.database import Base
    Base.metadata.create_all(bind=db.get_bind())

    # 0. Ensure Technical Course Lab Templates are seeded even if curriculum exists
    from app.modules.technical_courses.services.template_service import BUILTIN_LAB_TEMPLATES
    from app.models.models import TechnicalLabTemplate
    
    if not db.query(TechnicalLabTemplate).first():
        for t in BUILTIN_LAB_TEMPLATES:
            tc_json = json.dumps([tc.model_dump() for tc in t.test_cases_template])
            tmpl_record = TechnicalLabTemplate(
                id=t.id,
                title=t.title,
                skill=t.skill,
                language=t.language,
                difficulty=t.difficulty,
                lab_type=t.lab_type,
                tags_json=json.dumps(t.tags),
                instructions_template=t.instructions_template,
                starter_code_template=t.starter_code_template,
                solution_template=t.solution_template,
                constraints_json=json.dumps(t.constraints),
                test_cases_template_json=tc_json
            )
            db.merge(tmpl_record)
        db.commit()

    # Check if already seeded base data
    if db.query(User).first():
        sync_course_curriculum_videos(db)
        seed_digital_governance_curriculum(db)
        seed_cybersec_challenges(db)
        return

    print("Seeding iGot Karmayogi database with official civil service curriculum...")

    # 1. Departments
    depts = [
        Department(name="Ministry of Statistics & Programme Implementation (MoSPI)", description="National statistical authority"),
        Department(name="National Sample Survey Office (NSSO)", description="Socio-economic sample surveys division"),
        Department(name="Central Statistics Office (CSO)", description="National accounts and price indices division"),
        Department(name="Institute of Secretariat Training & Management (ISTM)", description="Civil services management institute"),
        Department(name="Department of Personnel & Training (DoPT)", description="Civil services administrative cadre")
    ]
    db.add_all(depts)
    db.commit()

    # 2. Skills (4 Core Competency Verticals)
    skills_data = [
        ("Civil Service Conduct Rules & Administrative Ethics", "Behavioural Competency"),
        ("Consumer Price Index (CPI) & Inflation Analysis", "Statistical Competency"),
        ("Data Cleaning, Wrangling & Python Automation", "Technical Competency"),
        ("Cybersecurity Defense & Digital Public Infrastructure", "Digital Governance")
    ]
    skills = []
    for name, cat in skills_data:
        s = Skill(name=name, category=cat)
        db.add(s)
        skills.append(s)
    db.commit()

    # 3. Users
    admin_user = User(
        email="admin@karmayogi.gov.in",
        password_hash=get_password_hash("Admin@123"),
        full_name="Dr. Arvind Subramanian",
        role="admin"
    )
    db.add(admin_user)
    db.flush()

    admin_profile = UserProfile(
        user_id=admin_user.id,
        phone="+91 98100 12345",
        bio="Director General, National Statistical Systems Training Academy (NSSTA). Oversight of capacity building for Indian Statistical Service (ISS) officers.",
        education="Ph.D. in Econometrics, Delhi School of Economics",
        work_experience_years=22,
        prior_training="LBSNAA Senior Leadership Program, IMF National Accounts Fellowship",
        designation="Director General",
        department="Ministry of Statistics & Programme Implementation (MoSPI)",
        job_role="Institutional Capacity & Training Administrator",
        current_assignment="Oversight of ISS Cadre Training & Karmayogi Statistical Curriculum",
        areas_of_interest="National Accounts, Capacity Building, Data Governance",
        language_pref="en",
        appearance_pref="light",
        onboarding_completed=True,
        daily_goal_minutes=45,
        current_streak_days=14
    )
    db.add(admin_profile)

    learner_user = User(
        email="rajesh.kumar@mospi.gov.in",
        password_hash=get_password_hash("Learner@123"),
        full_name="Rajesh Kumar",
        role="learner"
    )
    db.add(learner_user)
    db.flush()

    learner_profile = UserProfile(
        user_id=learner_user.id,
        phone="+91 98765 43210",
        bio="Senior Statistical Officer in National Accounts Division, MoSPI. Passionate about price statistics and automated sample validation.",
        education="M.Sc. Statistics, Banaras Hindu University",
        work_experience_years=8,
        prior_training="NSSTA Foundation Course, ISTM Public Procurement",
        designation="Senior Statistical Officer (SSO)",
        department="Central Statistics Office (CSO)",
        job_role="Price Indices and Monthly CPI Compilation",
        current_assignment="Urban Consumer Basket Weight Revision 2026",
        areas_of_interest="Inflation Metrics, Sample Survey Design, Python Automation",
        language_pref="en",
        appearance_pref="light",
        onboarding_completed=True,
        daily_goal_minutes=30,
        current_streak_days=6
    )
    db.add(learner_profile)

    new_user = User(
        email="priya.sharma@mospi.gov.in",
        password_hash=get_password_hash("Learner@123"),
        full_name="Priya Sharma",
        role="learner"
    )
    db.add(new_user)
    db.flush()

    new_profile = UserProfile(
        user_id=new_user.id,
        phone="+91 99112 88344",
        bio="Assistant Director (ISS 2024 Batch), NSSO Field Operations Division.",
        education="M.Stat, Indian Statistical Institute (ISI) Kolkata",
        work_experience_years=2,
        prior_training="Foundation Course at LBSNAA",
        designation="Assistant Director",
        department="National Sample Survey Office (NSSO)",
        job_role="Field Survey Supervision & Quality Control",
        onboarding_completed=False,  # Triggers 5-step wizard on first login!
        daily_goal_minutes=30,
        current_streak_days=1
    )
    db.add(new_profile)
    db.commit()

    # 4. Courses (4 Core Competency Verticals)
    # Course 1: Behavioural Competency
    c1 = Course(
        title="Civil Service Conduct, Administrative Ethics & Interpersonal Leadership",
        overview="Master statutory administrative ethics, CCS (Conduct) Rules 1964, Rule 14 disciplinary inquiries, natural justice doctrines, public grievance redressal, high-stakes stakeholder negotiation, and oral civil service defense.",
        instructor="Smt. Rashmi Verma, IAS (Retd.) & Shri P. K. Basu",
        organization="Department of Personnel & Training (DoPT)",
        duration_hours=6.0,
        difficulty="intermediate",
        source="internal",
        category="Behavioural",
        rating=4.92,
        enrolled_count=1850,
        is_popular=True,
        is_new=True
    )
    db.add(c1)
    db.flush()

    m1_1 = Module(course_id=c1.id, title="Module 1: Statutory Code of Conduct & Ethics", description="CCS (Conduct) Rules 1964, integrity standards, and avoidance of conflict of interest.", order=1)
    m1_2 = Module(course_id=c1.id, title="Module 2: Quasi-Judicial Inquiries & Natural Justice", description="Conducting departmental proceedings under Rule 14 CCS (CCA) Rules.", order=2)
    m1_3 = Module(course_id=c1.id, title="Module 3: Administrative Negotiation & Public Leadership", description="High-pressure public communication, grievance redressal, and crisis leadership.", order=3)
    db.add_all([m1_1, m1_2, m1_3])
    db.flush()

    l1_1_1 = Lesson(
        module_id=m1_1.id,
        title="Lesson 1: Statutory Framework of CCS (Conduct) Rules, 1964",
        content_type="video",
        duration_minutes=20,
        video_url="https://www.youtube.com/watch?v=hPGz-XBfVbM",
        content="""# Statutory Framework of CCS (Conduct) Rules, 1964

Every civil servant in the Government of India is governed by the statutory provisions of the **Central Civil Services (Conduct) Rules, 1964**:

1. **Rule 3 — General Principles of Integrity**:
   - Maintain absolute integrity, devotion to duty, and do nothing unbecoming of a Government servant.
   - Uphold supremacy of the Constitution and democratic values.
   - Defend impartiality, political neutrality, and fairness in administrative decision-making.

2. **Rule 3C — Prohibition of Sexual Harassment**:
   - Prevention of Sexual Harassment of Women at Workplace (POSH Act) compliance.
   - Timely constitution and facilitation of Internal Complaints Committees (ICC).

> **Doctrine**: Discretionary administrative powers must be exercised strictly within statutory limits, guided by public interest without personal or pecuniary bias.""",
        activity_question="Under Rule 3 of the CCS (Conduct) Rules, what is the paramount obligation of an administrative officer?",
        activity_options_json=json.dumps([
            "To maintain absolute integrity, devotion to duty, and political neutrality",
            "To obey verbal instructions from non-official acquaintances",
            "To maximize fee collections arbitrarily",
            "To bypass statutory tender processes"
        ]),
        activity_correct_option=0,
        activity_explanation="Rule 3(1) mandates absolute integrity, dedication to duty, and conduct worthy of an officer of the State.",
        order=1
    )

    l1_1_2 = Lesson(
        module_id=m1_1.id,
        title="Lesson 2: Ethical Decision Making & Conflict of Interest",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=F7p3z9H1BbM",
        content="""# Ethical Decision Making & Managing Conflicts of Interest

Public trust relies on the transparent declaration and mitigation of actual, potential, or perceived conflicts of interest.

### Key Tenets:
- **Recusal Mandate**: An officer must recuse themselves from any procurement, hiring, or regulatory decision involving family or commercial associations.
- **Gifts & Hospitality (Rule 13)**: Acceptance of gifts beyond prescribed statutory monetary thresholds requires prior sanction or intimation.
- **Post-Retirement Employment (Rule 10)**: Strict cooling-off periods apply before taking commercial roles related to past official dealings.""",
        activity_question="When an official matter involves an entity where a relative holds a financial interest, what is the correct procedural action?",
        activity_options_json=json.dumps([
            "Formally disclose the relationship in writing and recuse from the decision-making process",
            "Proceed with the file if no monetary gain is directly transferred",
            "Keep the information confidential to avoid administrative delays",
            "Delegate the decision verbally to a junior staff member"
        ]),
        activity_correct_option=0,
        activity_explanation="Administrative ethics require explicit disclosure and formal recusal whenever a conflict of interest arises.",
        order=2
    )

    l1_2_1 = Lesson(
        module_id=m1_2.id,
        title="Lesson 3: Principles of Natural Justice (Audi Alteram Partem)",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=DLCUn6h7qRo",
        content="""# Audi Alteram Partem in Departmental Proceedings

In any quasi-judicial proceeding governed by Rule 14 of CCS (CCA) Rules, 1965:

1. **Right to Notice**:
   - Form 1 charge-sheet containing definite articles of charge, statement of imputations, and list of documents/witnesses.
2. **Right of Inspection**:
   - Under Rule 14(11), the Charged Officer must be permitted full physical or certified digital access to listed documentary evidence.
3. **Impartial Inquiring Authority**:
   - The IA acts as an independent quasi-judicial evaluator, not a prosecutor.""",
        activity_question="What does the doctrine of Audi Alteram Partem require during a Rule 14 inquiry?",
        activity_options_json=json.dumps([
            "Granting fair hearing and opportunity to inspect evidence and cross-examine witnesses",
            "Allowing the prosecution to hide confidential witness statements",
            "Ordering immediate punishment without recording evidence",
            "Conducting ex-parte hearings without notice"
        ]),
        activity_correct_option=0,
        activity_explanation="Audi Alteram Partem guarantees no person shall be condemned unheard, requiring evidence disclosure and right of defense.",
        order=1
    )

    l1_3_1 = Lesson(
        module_id=m1_3.id,
        title="Lesson 4: Public Grievance Redressal & Crisis Negotiation",
        content_type="video",
        duration_minutes=20,
        video_url="https://www.youtube.com/watch?v=HAnw168huqA",
        content="""# Public Grievance Redressal & Crisis Stakeholder Negotiation

Civil servants frequently navigate high-stakes community grievances, public protests, and emergency stakeholder meetings.

### Core Frameworks:
1. **Active Listening & De-escalation**:
   - Acknowledge legitimate concerns without making ultra vires statutory commitments.
2. **CPGRAMS Time-bound Resolution**:
   - Strict adherence to the 21-day timeline for citizen grievance redressal with reasoned speaking orders.
3. **Multi-Stakeholder Consensus**:
   - Balancing statutory regulatory compliance with empathy and public interest.""",
        activity_question="Under standard administrative guidelines, how should a citizen grievance on CPGRAMS be concluded?",
        activity_options_json=json.dumps([
            "With a reasoned speaking order explaining the statutory grounds and redressal action taken",
            "With a generic one-line closure note without inspection",
            "By forwarding the grievance indefinitely between departments",
            "By closing the ticket after 48 hours automatically"
        ]),
        activity_correct_option=0,
        activity_explanation="Grievance disposal requires a reasoned speaking order transparently outlining the statutory resolution.",
        order=1
    )
    db.add_all([l1_1_1, l1_1_2, l1_2_1, l1_3_1])
    db.flush()

    # Course 2: Statistical Competency
    c2 = Course(
        title="Compilation of Consumer Price Index (CPI) & Inflation Metrics",
        overview="Comprehensive practical guide to the compilation of All India Consumer Price Index (Rural, Urban, Combined). Learn item basket weighting, Laspeyres index formulation, geometric mean of price relatives, treatment of seasonal goods, and house rent imputation.",
        instructor="Dr. P. C. Mohanan & Shri Sunil Jain",
        organization="Central Statistics Office (CSO)",
        duration_hours=5.0,
        difficulty="advanced",
        source="internal",
        category="Statistical",
        rating=4.88,
        enrolled_count=1420,
        is_popular=True,
        is_new=False
    )
    db.add(c2)
    db.flush()

    m2_1 = Module(course_id=c2.id, title="Module 1: Index Formulation & Basket Selection", description="Mathematical foundations of modified Laspeyres and Jevons price relatives.", order=1)
    m2_2 = Module(course_id=c2.id, title="Module 2: Imputation & Quality Adjustment", description="Techniques for disappearing items, seasonal goods, and rent imputation.", order=2)
    m2_3 = Module(course_id=c2.id, title="Module 3: Inflation Analytics & Policy Applications", description="Headline vs core inflation metrics and monetary policy coordination.", order=3)
    db.add_all([m2_1, m2_2, m2_3])
    db.flush()

    l2_1_1 = Lesson(
        module_id=m2_1.id,
        title="Lesson 1: The Modified Laspeyres Price Index Formula",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=L2OochgcO3E",
        content="""# The Modified Laspeyres Formula in CPI Compilation

In India's official CPI (Base 2012=100), elementary price indices are aggregated using a **Modified Laspeyres Formula**:

$$I = \\sum \\left[ W_i \\times \\left( \\frac{P_{i,t}}{P_{i,0}} \\right) \\right]$$

Where:
- $W_i$ is the normalized expenditure weight of item $i$ derived from the Consumer Expenditure Survey (CES).
- $P_{i,t}$ is the current period average price of item $i$.
- $P_{i,0}$ is the base year price of item $i$.

### Elementary Aggregation with Jevons
At the market level, price quotations for a specific item across multiple selected shops are aggregated using the **Geometric Mean (Jevons Index)** rather than the simple arithmetic mean to prevent upward substitution bias.""",
        activity_question="Which index formula is employed at the elementary quotation level to minimize substitution bias?",
        activity_options_json=json.dumps([
            "Geometric Mean (Jevons Index)",
            "Simple Harmonic Mean",
            "Carli Arithmetic Index",
            "Dutot Ratio of Averages"
        ]),
        activity_correct_option=0,
        activity_explanation="International best practices and MoSPI guidelines use the Geometric Mean (Jevons) at the elementary quotation level because it exhibits transitivity and minimizes substitution bias.",
        order=1
    )

    l2_1_2 = Lesson(
        module_id=m2_1.id,
        title="Lesson 2: Elementary Price Relatives & Weight Aggregation",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=KwS0XZb4qGA",
        content="""# Elementary Price Relatives & Weight Aggregation

Price relatives represent the ratio of the current price of a commodity to its base price:

$$R_{i} = \\frac{P_{i,t}}{P_{i,0}} \\times 100$$

### Aggregation Pipeline:
1. **Market Quotation Collection**: 1,181 village markets and 1,114 urban markets surveyed across India.
2. **Sub-group Indices**: Aggregating items (e.g., Cereals, Pulses, Fuel, Housing).
3. **All-India Combined Index**: State-level indices aggregated using consumption expenditure weights.""",
        activity_question="If an item with base price Rs. 80 is sold at Rs. 100 in period t, what is its elementary price relative?",
        activity_options_json=json.dumps([
            "125.0",
            "80.0",
            "120.0",
            "105.0"
        ]),
        activity_correct_option=0,
        activity_explanation="Price Relative = (100 / 80) * 100 = 125.0",
        order=2
    )

    l2_2_1 = Lesson(
        module_id=m2_2.id,
        title="Lesson 3: Handling Disappearing Quotations & House Rent Imputation",
        content_type="video",
        duration_minutes=20,
        video_url="https://www.youtube.com/watch?v=RuNp3l_2dGs",
        content="""# Imputation Techniques for Missing Price Quotations

When selected items are temporarily unavailable in local markets:

1. **Class Mean Imputation**: Imputing the missing price change using the average price change of available items within the same sub-group.
2. **Chain Relative Imputation**: Linking short-term price movements to preserve continuity.
3. **Repeat Rent Survey**: Semi-annual survey of identical rented dwellings to track pure rental inflation without quality changes.""",
        activity_question="When a specific vegetable variety is temporarily unavailable in a market, which imputation method is standard?",
        activity_options_json=json.dumps([
            "Imputing the price trend from the available varieties in the same sub-group",
            "Setting the price to zero",
            "Using the highest price recorded across all states",
            "Deleting the entire commodity from the state basket"
        ]),
        activity_correct_option=0,
        activity_explanation="Class mean imputation uses the subgroup price trend to estimate missing quotations accurately.",
        order=1
    )
    db.add_all([l2_1_1, l2_1_2, l2_2_1])
    db.flush()

    # Course 3: Technical Competency
    c3 = Course(
        title="Python and Data Cleaning Pipelines for Public Policy",
        overview="Modern automated data cleaning and reproducible data processing for civil service analysts using Pandas, NumPy, and Statsmodels. Automate messy survey ingestion, missing data imputation, schema validation, and pipeline orchestration.",
        instructor="Dr. Tanvi Grover & Prof. Rajesh Sen",
        organization="MoSPI Data Lab",
        duration_hours=8.0,
        difficulty="intermediate",
        source="internal",
        category="Technical",
        rating=4.95,
        enrolled_count=1680,
        is_popular=True,
        is_new=True
    )
    db.add(c3)
    db.flush()

    m3_1 = Module(
        course_id=c3.id,
        title="Module 1: Comprehensive Python & Data Wrangling Masterclass",
        description="Complete masterclass video lecture covering Python microdata data structures, vectorized Pandas operations, missing value imputation, and Pydantic validation.",
        order=1
    )
    m3_2 = Module(
        course_id=c3.id,
        title="Module 2: Hands-on Practice, Coding Labs & Assessment",
        description="Interactive Jupyter coding workspaces, automated Pytest assertions, data-wrangling challenges, and final certification exam.",
        order=2
    )
    db.add_all([m3_1, m3_2])
    db.flush()

    # Module 1 Lessons
    l3_1_1 = Lesson(
        module_id=m3_1.id,
        title="Lesson 1: Python Fundamentals & Data Handling for Policy Analysts",
        topic="Python Data Structures & Policy Microdata",
        learning_objective="Master Python core data structures, memory layouts, and dictionary-based record processing for public policy datasets.",
        source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
        content_type="video",
        duration_minutes=40,
        video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
        video_start_time=0,
        video_end_time=2400,
        content="""# Python Fundamentals & Microdata Structures

When processing administrative returns and household survey data, selecting optimal in-memory data structures prevents memory blowups and slow iteration times.""",
        activity_question="Which Python data structure provides O(1) average-time lookups by unique identifier?",
        activity_options_json=json.dumps([
            "Dictionary (dict / hash map)",
            "Unsorted List",
            "Nested Tuple",
            "Linked File Buffer"
        ]),
        activity_correct_option=0,
        activity_explanation="Python dictionaries utilize hash tables offering O(1) average lookup time.",
        order=1
    )

    l3_1_2 = Lesson(
        module_id=m3_1.id,
        title="Lesson 2: Vectorized Data Wrangling with Pandas",
        topic="Pandas Vectorization vs Iterative Loops",
        learning_objective="Implement vectorized series operations and Boolean masking on administrative tables without slow Python interpreter loops.",
        source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
        content_type="video",
        duration_minutes=45,
        video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
        video_start_time=2400,
        video_end_time=5400,
        content="""# Vectorized Data Wrangling with Pandas

When processing large-scale public policy microdata, vectorized Pandas calculations delegate execution to compiled NumPy C routines, yielding massive performance speedups over iterative loops.""",
        activity_question="Why should vectorized methods be preferred over row-by-row for-loops in Pandas?",
        activity_options_json=json.dumps([
            "Vectorized calculations run in compiled C routines and are orders of magnitude faster",
            "Because for-loops are deprecated in Python 3.12",
            "Because vectorized methods use less hard disk space",
            "Because Pandas does not support for-loops"
        ]),
        activity_correct_option=0,
        activity_explanation="Pandas vectorization delegates calculations to compiled NumPy C routines without Python interpreter loop overhead.",
        order=2
    )

    l3_1_3 = Lesson(
        module_id=m3_1.id,
        title="Lesson 3: Missing Value Treatment, Outlier Detection & Multiplier Scaling",
        topic="Missing Value Imputation & Survey Multipliers",
        learning_objective="Sanitize survey missing sentinel codes, scale sampling weights, and calculate weighted population statistics.",
        source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
        content_type="video",
        duration_minutes=40,
        video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
        video_start_time=5400,
        video_end_time=8400,
        content="""# Cleaning Missing Values and Applying Sampling Multipliers

In NSSO and PLFS microdata:
- Missing survey codes (`999`, `-1`, or blank) must be cleanly converted to `NaN`.
- Multipliers (weights) must be divided by the appropriate sub-sample scale factor (e.g., `100` or `1000`).

```python
# Cleaning sentinel missing codes
df["income"] = df["income"].replace([999999, -1], np.nan)

# Weighted mean income calculation
weighted_mean = (df["income"] * df["multiplier"]).sum() / df["multiplier"].sum()
```""",
        activity_question="How should survey sentinel missing values (such as 999999) be handled before statistical calculation?",
        activity_options_json=json.dumps([
            "Replaced with NaN and handled via explicit masking or domain-approved imputation",
            "Included directly in standard sum and average calculations",
            "Replaced with zero without documenting the change",
            "Ignored by multiplying all rows by 0"
        ]),
        activity_correct_option=0,
        activity_explanation="Sentinel codes must be converted to NaN to prevent disastrous distortions in statistical aggregations.",
        order=3
    )

    l3_1_4 = Lesson(
        module_id=m3_1.id,
        title="Lesson 4: Administrative Schema Validation with Pydantic & Regex",
        topic="Pydantic Schema Validation & Regex Parsing",
        learning_objective="Validate administrative data against typed Pydantic models with custom field validators and regular expressions.",
        source_video_title="CodeWithHarry - Python Programming & Data Structures Masterclass",
        content_type="video",
        duration_minutes=40,
        video_url="https://www.youtube.com/watch?v=UrsmFxEIp5k",
        video_start_time=8400,
        video_end_time=11400,
        content="""# Schema Validation & Regex for Administrative Returns

Government datasets received from district offices often suffer from format drift, incorrect State/District LGD codes, and invalid dates.

```python
from pydantic import BaseModel, Field, field_validator
import re

class BeneficiaryRecord(BaseModel):
    state_lgd_code: int = Field(ge=1, le=38)
    beneficiary_id: str
    amount_disbursed: float = Field(ge=0)

    @field_validator("beneficiary_id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{2}\\d{8}$", v):
            raise ValueError("Invalid Beneficiary ID format (expected 2 letters followed by 8 digits)")
        return v
```""",
        activity_question="What is the primary advantage of validating data with Pydantic schemas before running analytics?",
        activity_options_json=json.dumps([
            "Catches schema drift, invalid values, and bad types before corrupt data enters downstream pipelines",
            "Eliminates the need to ever back up the database",
            "Converts all data to binary files automatically",
            "Bypasses database constraints completely"
        ]),
        activity_correct_option=0,
        activity_explanation="Pydantic guarantees strict runtime type and constraint enforcement, stopping bad data at the boundary.",
        order=4
    )

    # Module 2 Lessons (Practice, Labs & Assessment)
    l3_2_1 = Lesson(
        module_id=m3_2.id,
        title="Lesson 1: Python & Pandas Knowledge Check (Quiz)",
        topic="Python & Pandas Conceptual Assessment",
        learning_objective="Test conceptual mastery of vectorized computations, memory optimization, and data structures.",
        content_type="reading",
        duration_minutes=15,
        content="""# Python & Pandas Conceptual Knowledge Check

Review your theoretical and syntactic mastery before entering the live coding lab workspace.""",
        activity_question="Why do vectorized Pandas calculations vastly outperform Python for-loops on large survey microdata?",
        activity_options_json=json.dumps([
            "Vectorized operations delegate execution to compiled NumPy C routines without Python interpreter overhead",
            "Because Python for-loops are not allowed in data science",
            "Because vectorized operations convert data to text files",
            "Because loops consume more internet bandwidth"
        ]),
        activity_correct_option=0,
        activity_explanation="Pandas vectorization delegates calculations directly to compiled C code without GIL and loop overhead.",
        order=1
    )

    l3_2_2 = Lesson(
        module_id=m3_2.id,
        title="Lesson 2: Hands-on Lab: Survey Multiplier Scaling & Weight Imputation",
        topic="Pandas Data Cleaning & Aggregation Pipeline",
        learning_objective="Write and execute an end-to-end Pandas data cleaning pipeline calculating weighted population mean income in the interactive sandbox.",
        content_type="lab",
        duration_minutes=30,
        content="""# Hands-on Lab: Survey Multiplier Scaling & Weight Imputation

In this executable lab, you will load a survey dataset, sanitize `-1` and `999999` sentinel missing codes, scale the multiplier weights, and calculate weighted population income metrics.

```python
import pandas as pd
import numpy as np

def clean_survey_data(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Convert missing sentinels to NaN
    df['income'] = df['income'].replace([999999, -1], np.nan)
    # 2. Scale multiplier weight
    df['multiplier_scaled'] = df['multiplier'] / 100.0
    return df
```

Launch the lab workspace below to run and test your implementation with live Pytest assertions.""",
        activity_question="In PLFS survey microdata, what is the role of the multiplier field?",
        activity_options_json=json.dumps([
            "It represents the inverse probability weight to project sample observations to the total population",
            "It multiplies the execution speed of the CPU",
            "It acts as a random encryption salt",
            "It has no statistical meaning"
        ]),
        activity_correct_option=0,
        activity_explanation="Sampling multipliers are expansion weights that inflate sample records to population estimates.",
        order=2
    )

    l3_2_3 = Lesson(
        module_id=m3_2.id,
        title="Lesson 3: Hands-on Lab: Administrative Schema Validation with Pydantic",
        topic="Pydantic Schema Validation & Exception Handling",
        learning_objective="Implement and execute Pydantic model validators and regular expression checks on district records in the interactive sandbox.",
        content_type="lab",
        duration_minutes=30,
        content="""# Hands-on Lab: Administrative Schema Validation

Implement runtime type and constraint enforcement for government district returns using Pydantic.

```python
from pydantic import BaseModel, Field, field_validator
import re

class DistrictRecord(BaseModel):
    state_code: int = Field(ge=1, le=38)
    beneficiary_id: str
    amount_disbursed: float = Field(ge=0)

    @field_validator('beneficiary_id')
    @classmethod
    def check_id_format(cls, v: str) -> str:
        if not re.match(r'^[A-Z]{2}\\d{8}$', v):
            raise ValueError('Beneficiary ID must be 2 uppercase letters followed by 8 digits')
        return v
```

Launch the lab workspace below to run and test your schema with live test cases.""",
        activity_question="Which Pydantic decorator allows custom validation logic on specific attributes?",
        activity_options_json=json.dumps([
            "@field_validator",
            "@check_column",
            "@assert_valid",
            "@db_column"
        ]),
        activity_correct_option=0,
        activity_explanation="Pydantic V2 uses the @field_validator decorator for custom validation functions.",
        order=3
    )

    l3_2_4 = Lesson(
        module_id=m3_2.id,
        title="Lesson 4: Hands-on Lab: Policy Visualizations & Statistical Summaries",
        topic="Matplotlib & Seaborn Policy Dashboards",
        learning_objective="Generate automated policy distribution plots and quartile binning charts for administrative reporting in the interactive sandbox.",
        content_type="lab",
        duration_minutes=30,
        content="""# Hands-on Lab: Policy Visualizations

Generate standardized distribution plots, box plots, and summary metrics for district welfare allocations.

```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def plot_welfare_distribution(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(x='district_name', y='disbursed_amount', data=df, ax=ax)
    ax.set_title('Welfare Disbursement Distribution across Districts')
    return fig
```

Launch the lab workspace below to execute and verify your chart generation code.""",
        activity_question="Which chart is standard for identifying interquartile ranges and outlier values across districts?",
        activity_options_json=json.dumps([
            "Box and Whisker Plot (Boxplot)",
            "Simple Pie Chart",
            "Radial Gauge",
            "Network Flow Graph"
        ]),
        activity_correct_option=0,
        activity_explanation="Box plots show quartiles, median line, and individual outlier markers distinctly.",
        order=4
    )

    db.add_all([l3_1_1, l3_1_2, l3_1_3, l3_1_4, l3_2_1, l3_2_2, l3_2_3, l3_2_4])
    db.flush()

    # Course 4: Digital Governance (Full Official Curriculum with 5 Modules & 10 Lessons)
    seed_digital_governance_curriculum(db)
    c4 = db.query(Course).filter(Course.title == "Digital Governance, Cyber Defense & Public Digital Architecture").first()

    # Link Course Skills
    cs_links = [
        (c1.id, skills[0].id),
        (c2.id, skills[1].id),
        (c3.id, skills[2].id),
    ]
    for cid, sid in cs_links:
        db.add(CourseSkill(course_id=cid, skill_id=sid))
    if c4:
        db.add(CourseSkill(course_id=c4.id, skill_id=skills[3].id))
    db.commit()

    # 5. Assessments for Courses
    # Assessment 1 for Course 1 (Behavioural)
    a1 = Assessment(
        course_id=c1.id,
        title="Certification Exam: Civil Service Conduct & Administrative Ethics",
        description="Official certification examination testing statutory integrity standards, CCS (Conduct) Rules 1964, natural justice principles, and Rule 14 inquiry procedures.",
        time_limit_minutes=25,
        pass_threshold_percent=70.0
    )
    db.add(a1)
    db.flush()

    q1_1 = Question(
        assessment_id=a1.id,
        text="Under Rule 14(11) of the CCS (CCA) Rules 1965, what right does the Charged Officer have regarding documentary evidence?",
        options_json=json.dumps([
            "Absolute right to inspect and receive certified copies of listed prosecution documents",
            "No right to inspect documents until final judgment",
            "Only verbal summary by the Presenting Officer",
            "Inspection permitted only after prosecution concludes witnesses"
        ]),
        correct_option_index=0,
        explanation="Rule 14(11) guarantees the statutory right of the Charged Officer to inspect listed documents to prepare their defense.",
        order=1
    )
    q1_2 = Question(
        assessment_id=a1.id,
        text="What is the consequence if an Inquiring Authority proceeds ex-parte after a formal application alleging bias has been filed?",
        options_json=json.dumps([
            "Proceedings are fatally vitiated for violating Audi Alteram Partem and will be quashed",
            "The inquiry is accelerated lawfully",
            "The officer automatically forfeits defense rights",
            "The Inquiring Authority receives special commendation"
        ]),
        correct_option_index=0,
        explanation="Per established DoPT guidelines and judicial precedents, the IA must stay proceedings until the Disciplinary Authority decides the bias petition.",
        order=2
    )
    q1_3 = Question(
        assessment_id=a1.id,
        text="Under Rule 3 of CCS (Conduct) Rules, which duty is expressly mandated for every civil servant?",
        options_json=json.dumps([
            "To maintain absolute integrity, devotion to duty, and do nothing unbecoming of a Government servant",
            "To prioritize personal commercial interests over official tasks",
            "To disclose classified statistical releases prematurely",
            "To accept costly gifts from contracting vendors"
        ]),
        correct_option_index=0,
        explanation="Rule 3(1) is the core ethical obligation binding all central government employees.",
        order=3
    )
    q1_4 = Question(
        assessment_id=a1.id,
        text="When can a disciplinary authority dispense with a departmental inquiry before imposing major penalties?",
        options_json=json.dumps([
            "Only under exceptional conditions covered strictly under Article 311(2) second proviso of the Constitution",
            "Whenever the inquiry would take more than one week",
            "If the accused officer submits a written denial",
            "At the arbitrary verbal instruction of an administrative head"
        ]),
        correct_option_index=0,
        explanation="Article 311(2) proviso strictly delineates the rare constitutional exceptions (e.g. state security or impracticability).",
        order=4
    )
    db.add_all([q1_1, q1_2, q1_3, q1_4])
    db.flush()

    # Assessment 2 for Course 2
    a2 = Assessment(
        course_id=c2.id,
        title="Certification Exam: Consumer Price Index (CPI) Compilation",
        description="Assesses mastery of price aggregation, Laspeyres index methodology, and outlier handling.",
        time_limit_minutes=20,
        pass_threshold_percent=70.0
    )
    db.add(a2)
    db.flush()

    q2_1 = Question(
        assessment_id=a2.id,
        text="At the elementary price quotation level, which average is recommended to eliminate upward substitution bias?",
        options_json=json.dumps([
            "Geometric Mean (Jevons Index)",
            "Harmonic Mean",
            "Simple Arithmetic Mean (Carli)",
            "Mode of reported prices"
        ]),
        correct_option_index=0,
        explanation="The geometric mean (Jevons) satisfies axiomatic time-reversal and treats price relatives symmetrically, minimizing substitution bias.",
        order=1
    )
    q2_2 = Question(
        assessment_id=a2.id,
        text="The item basket weights in the All-India CPI are fundamentally derived from which statistical source?",
        options_json=json.dumps([
            "Household Consumer Expenditure Survey (CES / HCES)",
            "Annual Survey of Industries (ASI)",
            "Reserve Bank of India Monetary Policy Report",
            "Census decennial headcounts"
        ]),
        correct_option_index=0,
        explanation="CPI item weights reflect consumer spending patterns measured directly in the nationwide Household Consumer Expenditure Survey.",
        order=2
    )
    db.add_all([q2_1, q2_2])
    db.commit()

    # 6. Active Enrollment & Progress for Learner Rajesh Kumar
    enr1 = Enrollment(
        user_id=learner_user.id,
        course_id=c1.id,
        status="in_progress",
        started_at=datetime.datetime.utcnow() - datetime.timedelta(days=4),
        progress_percent=66.7,
        last_lesson_id=l1_1_2.id
    )
    db.add(enr1)
    db.flush()

    prog1 = Progress(enrollment_id=enr1.id, module_id=m1_1.id, lesson_id=l1_1_1.id, completed=True, activity_completed=True)
    prog2 = Progress(enrollment_id=enr1.id, module_id=m1_1.id, lesson_id=l1_1_2.id, completed=True, activity_completed=True)
    db.add_all([prog1, prog2])

    # Planned Course for Learner
    p_course = PlannedCourse(
        user_id=learner_user.id,
        course_id=c2.id,
        planned_for="Q4 2026",
        source="self"
    )
    db.add(p_course)

    # Learning History
    lh1 = LearningHistory(user_id=learner_user.id, course_id=c1.id, viewed_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2))
    lh2 = LearningHistory(user_id=learner_user.id, course_id=c3.id, viewed_at=datetime.datetime.utcnow() - datetime.timedelta(days=1))
    db.add_all([lh1, lh2])

    # Seed User Skill
    us1 = UserSkill(user_id=learner_user.id, skill_id=skills[2].id, source_course_id=c3.id)
    db.add(us1)

    # 10. Seed Technical Course Lab Templates (Human-Created)
    from app.modules.technical_courses.services.template_service import BUILTIN_LAB_TEMPLATES
    from app.models.models import TechnicalLabTemplate
    
    for t in BUILTIN_LAB_TEMPLATES:
        tc_json = json.dumps([tc.model_dump() for tc in t.test_cases_template])
        tmpl_record = TechnicalLabTemplate(
            id=t.id,
            title=t.title,
            skill=t.skill,
            language=t.language,
            difficulty=t.difficulty,
            lab_type=t.lab_type,
            tags_json=json.dumps(t.tags),
            instructions_template=t.instructions_template,
            starter_code_template=t.starter_code_template,
            solution_template=t.solution_template,
            constraints_json=json.dumps(t.constraints),
            test_cases_template_json=tc_json
        )
        db.merge(tmpl_record)

    # 11. Seed Digital Governance Challenges
    seed_cybersec_challenges(db)

    db.commit()
    print("Database successfully seeded with realistic civil service curriculum, accounts, technical lab templates, and digital governance challenges!")
