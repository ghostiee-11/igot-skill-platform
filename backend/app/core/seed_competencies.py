import logging
from sqlalchemy.orm import Session
from app.models.models import CompetencyDomain, Competency, EvidenceCompetencyMapping, User, UserCompetencyScore, GapAnalysis

logger = logging.getLogger(__name__)

DOMAINS = [
    ("statistical", "Statistical Competencies", "Survey design, sampling, national accounts, and official statistics methodology."),
    ("technical", "Technical Competencies", "Programming, data tooling, cloud, and AI/ML skills."),
    ("digital_governance", "Digital Governance", "Cybersecurity, data privacy, and government digital infrastructure."),
    ("behavioural", "Behavioural & Managerial", "Leadership, communication, ethics, and decision making."),
]

COMPETENCIES = {
    "statistical": [
        ("statistical_survey_design", "Survey Design"),
        ("statistical_sampling", "Sampling"),
        ("statistical_national_accounts", "National Accounts"),
        ("statistical_price_statistics", "Price Statistics"),
        ("statistical_labour_statistics", "Labour Statistics"),
        ("statistical_agricultural_statistics", "Agricultural Statistics"),
        ("statistical_industrial_statistics", "Industrial Statistics"),
        ("statistical_sdg_indicators", "SDG Indicators"),
        ("statistical_metadata_standards", "Metadata Standards"),
        ("statistical_data_quality", "Data Quality Frameworks"),
    ],
    "technical": [
        ("technical_python", "Python"),
        ("technical_r", "R"),
        ("technical_sql", "SQL"),
        ("technical_stata", "Stata"),
        ("technical_spss", "SPSS"),
        ("technical_sas", "SAS"),
        ("technical_gis", "GIS"),
        ("technical_data_visualization", "Data Visualization"),
        ("technical_ai_ml", "AI/ML"),
        ("technical_cloud_computing", "Cloud Computing"),
        ("technical_apis", "APIs"),
        ("technical_open_data", "Open Data"),
    ],
    "digital_governance": [
        ("digital_governance_cybersecurity", "Cybersecurity"),
        ("digital_governance_data_privacy", "Data Privacy"),
        ("digital_governance_digital_signatures", "Digital Signatures"),
        ("digital_governance_gov_cloud", "Government Cloud"),
        ("digital_governance_dpi", "Digital Public Infrastructure"),
    ],
    "behavioural": [
        ("behavioural_leadership", "Leadership"),
        ("behavioural_communication", "Communication"),
        ("behavioural_project_management", "Project Management"),
        ("behavioural_ethics", "Ethics"),
        ("behavioural_decision_making", "Decision Making"),
        ("behavioural_change_management", "Change Management"),
        ("behavioural_situational_awareness", "Situational Awareness"),
        ("behavioural_accountability", "Accountability"),
    ],
}


def seed_competency_taxonomy(db: Session) -> None:
    """Seeds the 4 competency domains and their competencies. Idempotent per-domain AND
    per-competency, so adding new competencies to an already-seeded domain (e.g. Phase 2's
    2 new behavioural competencies) still gets inserted on a DB where the domain already
    exists from an earlier seed run."""
    for code, name, description in DOMAINS:
        domain = db.query(CompetencyDomain).filter_by(code=code).first()
        if not domain:
            domain = CompetencyDomain(code=code, name=name, description=description)
            db.add(domain)
            db.flush()
        for comp_code, comp_name in COMPETENCIES[code]:
            existing_comp = db.query(Competency).filter_by(code=comp_code).first()
            if existing_comp:
                continue
            db.add(Competency(domain_id=domain.id, code=comp_code, name=comp_name, max_level=5))
    db.commit()


STAT_ENGINE_SKILL_TO_COMPETENCY_CODE = {
    "price.price_relative": "statistical_price_statistics",
    "price.cpi.weighted_price_relatives": "statistical_price_statistics",
    "price.fisher_index": "statistical_price_statistics",
    "price.inflation_rate": "statistical_price_statistics",
    "price.laspeyres_index": "statistical_price_statistics",
    "price.real_vs_nominal": "statistical_price_statistics",
}

STAT_ENGINE_COMPETENCY_TO_COMPETENCY_CODE = {
    "price_statistics": "statistical_price_statistics",
}

BEHAVIOURAL_NAME_TO_COMPETENCY_CODE = {
    "Leadership": "behavioural_leadership",
    "Communication": "behavioural_communication",
    "Project Management": "behavioural_project_management",
    "Ethics": "behavioural_ethics",
    "Decision Making": "behavioural_decision_making",
    "Change Management": "behavioural_change_management",
    "Ethical Judgement": "behavioural_ethics",  # carryforward's name for the same dimension interview calls "Ethics"
    "Situational Awareness": "behavioural_situational_awareness",
    "Accountability": "behavioural_accountability",
    # "Course Knowledge" is intentionally absent: it's interview-specific, not a taxonomy competency.
}


def seed_evidence_mapping(db: Session) -> None:
    """Seeds evidence_competency_mapping rows bridging stat_engine/behavioural string
    identifiers to real competencies.id rows. Idempotent. Requires seed_competency_taxonomy
    to have already run (reads Competency rows by code)."""
    def _upsert(source_system: str, source_key: str, competency_code: str) -> None:
        existing = db.query(EvidenceCompetencyMapping).filter_by(
            source_system=source_system, source_key=source_key
        ).first()
        if existing:
            return
        competency = db.query(Competency).filter_by(code=competency_code).first()
        if not competency:
            logger.warning(
                "seed_evidence_mapping: no Competency found for code=%s (source_system=%s, source_key=%s); "
                "skipping mapping rather than crashing startup. Taxonomy seed may not have run yet, or this is a typo.",
                competency_code, source_system, source_key,
            )
            return  # taxonomy not seeded yet or code typo; skip rather than crash startup
        db.add(EvidenceCompetencyMapping(
            source_system=source_system, source_key=source_key, competency_id=competency.id
        ))

    for skill_id, code in STAT_ENGINE_SKILL_TO_COMPETENCY_CODE.items():
        _upsert("stat_engine_skill", skill_id, code)
    for comp_id, code in STAT_ENGINE_COMPETENCY_TO_COMPETENCY_CODE.items():
        _upsert("stat_engine_competency", comp_id, code)
    for name, code in BEHAVIOURAL_NAME_TO_COMPETENCY_CODE.items():
        _upsert("behavioural_competency", name, code)

    db.commit()


def seed_demo_usage_evidence(db: Session) -> list[int]:
    """Give local/demo learners a believable cross-domain starting history.

    This is intentionally idempotent: real activity always wins, while an empty demo
    profile no longer renders as four zero-value competency cards.
    """
    seeded_user_ids: list[int] = []
    domain_levels = {
        "statistical": (3.4, 2.9, 3.1),
        "technical": (2.8, 3.2, 2.6),
        "digital_governance": (3.0, 2.5, 2.9),
        "behavioural": (3.6, 3.1, 3.3),
    }
    learners = db.query(User).filter(User.role != "admin").all()
    for user in learners:
        if db.query(UserCompetencyScore).filter_by(user_id=user.id).first():
            continue
        for domain_code, levels in domain_levels.items():
            domain = db.query(CompetencyDomain).filter_by(code=domain_code).first()
            if not domain:
                continue
            competencies = db.query(Competency).filter_by(domain_id=domain.id).order_by(Competency.id).limit(3).all()
            for competency, level in zip(competencies, levels):
                db.add(UserCompetencyScore(
                    user_id=user.id,
                    competency_id=competency.id,
                    level=level,
                    evidence_source="seeded_usage",
                ))
        seeded_user_ids.append(user.id)
    db.commit()
    return seeded_user_ids


def users_with_placeholder_gaps(db: Session) -> list[int]:
    """Return learners whose newest domain snapshot is still the all-zero placeholder."""
    user_ids: list[int] = []
    for user in db.query(User).filter(User.role != "admin").all():
        latest_by_domain = {}
        for gap in db.query(GapAnalysis).filter_by(user_id=user.id).order_by(GapAnalysis.generated_at.desc()).all():
            latest_by_domain.setdefault(gap.domain_id, gap)
        if not latest_by_domain or all(gap.current_level == 0 for gap in latest_by_domain.values()):
            user_ids.append(user.id)
    return user_ids
