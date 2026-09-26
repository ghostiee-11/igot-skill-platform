from copy import deepcopy


DOCUMENTS = [{
    "id": "doc_dopt_rule14_proceeding",
    "title": "Departmental Inquiry Proceeding under Rule 14 of CCS (CCA) Rules, 1965",
    "document_type": "Departmental Proceeding",
    "issuing_authority": "Department of Personnel & Training (DoPT), New Delhi",
    "document_number": "F.No. 11012/7/2025-Estt.(A-III)",
    "statutory_reference": "CCS (CCA) Rules, 1965 — Rules 14 and 15",
    "date_of_issue": "14 January 2026",
    "full_text": (
        "A charged officer must receive the articles of charge, supporting records and a reasonable "
        "opportunity to inspect evidence, present a defence and cross-examine witnesses before a major "
        "penalty is considered. The Inquiring Authority must record reasoned findings."
    ),
    "key_stakeholders": ["Disciplinary Authority", "Charged Officer", "Inquiring Authority", "Presenting Officer"],
    "procedural_clauses": [
        "Fifteen-day opportunity to submit a written defence",
        "Inspection of listed documents under Rule 14(11)",
        "Reasoned inquiry findings under Rule 14(23)",
    ],
}]


CASES = [{
    "id": "case_ccs_rule14_inquiry",
    "title": "Disciplinary Inquiry under Rule 14 CCS (CCA) Rules",
    "category": "Disciplinary Proceedings and Natural Justice",
    "course_id": 1,
    "course_title": "Civil Service Conduct, Administrative Ethics & Interpersonal Leadership",
    "course_organization": "Department of Personnel & Training (DoPT)",
    "document_id": "doc_dopt_rule14_proceeding",
    "document_title": DOCUMENTS[0]["title"],
    "document_type": DOCUMENTS[0]["document_type"],
    "statutory_citations": ["CCS (CCA) Rules, 1965 — Rule 14", "Constitution of India — Article 311(2)"],
    "initial_context": (
        "You are the Inquiring Authority for a major-penalty proceeding concerning premature disclosure "
        "of an official statistical release. The officer disputes the authenticity of email evidence."
    ),
    "root_question_id": "q_ccs_root",
    "questions": {
        "q_ccs_root": {
            "id": "q_ccs_root", "case_id": "case_ccs_rule14_inquiry", "stage_type": "root",
            "prompt": "The Presenting Officer asks to skip inspection of the original records. How should you rule?",
            "context_update": "Preliminary hearing before the Inquiring Authority.",
            "behavioral_competencies": ["procedural fairness", "decision making"],
            "options": [
                {"option_id": "A", "text": "Direct inspection of the original records before evidence is admitted.", "is_optimal": True, "is_satisfactory_terminal": True, "consequence_summary": "Natural justice and evidentiary integrity are preserved.", "statutory_rationale": "Rule 14(11) protects access to listed evidence.", "next_question_id": None},
                {"option_id": "B", "text": "Accept the printouts immediately to avoid delay.", "is_optimal": False, "is_satisfactory_terminal": False, "consequence_summary": "The officer objects to denial of a fair opportunity to defend.", "statutory_rationale": "Administrative speed cannot displace mandatory inspection rights.", "next_question_id": "q_ccs_recovery"},
            ],
        },
        "q_ccs_recovery": {
            "id": "q_ccs_recovery", "case_id": "case_ccs_rule14_inquiry", "stage_type": "carryforward_branch",
            "prompt": "How should you cure the procedural defect after the officer records an objection?",
            "context_update": "The proceeding must be restored to a fair evidentiary footing.",
            "behavioral_competencies": ["accountability", "conflict resolution"],
            "options": [
                {"option_id": "A", "text": "Pause the hearing, permit inspection and allow a supplementary defence.", "is_optimal": True, "is_satisfactory_terminal": True, "consequence_summary": "The defect is cured transparently.", "statutory_rationale": "A meaningful opportunity to respond restores procedural fairness.", "next_question_id": None},
                {"option_id": "B", "text": "Dismiss the objection without reasons.", "is_optimal": False, "is_satisfactory_terminal": True, "consequence_summary": "The inquiry remains vulnerable to review.", "statutory_rationale": "Unreasoned rejection conflicts with natural justice.", "next_question_id": None},
            ],
        },
    },
    "learning_objectives": ["Apply Rule 14 safeguards", "Recognize and cure natural-justice failures"],
}]


def all_cases(course_id: int | None = None) -> list[dict]:
    rows = CASES if course_id is None else [case for case in CASES if case.get("course_id") == course_id]
    return deepcopy(rows)


def find_case(case_id: str) -> dict | None:
    return next((deepcopy(case) for case in CASES if case["id"] == case_id), None)


def find_document(document_id: str) -> dict | None:
    return next((deepcopy(doc) for doc in DOCUMENTS if doc["id"] == document_id), None)
