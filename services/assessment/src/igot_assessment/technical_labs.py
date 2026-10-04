"""Public presentation of authored technical lab templates."""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import TechnicalLabTemplate


def template_catalogue(db: Session) -> list[tuple[int, TechnicalLabTemplate]]:
    templates = db.scalars(select(TechnicalLabTemplate).order_by(TechnicalLabTemplate.id)).all()
    return [(1001 + index, template) for index, template in enumerate(templates)]


def find_template(db: Session, lab_id: int | str) -> tuple[int, TechnicalLabTemplate] | tuple[None, None]:
    catalogue = template_catalogue(db)
    lab_str = str(lab_id).strip()
    if lab_str.isdigit():
        num_id = int(lab_str)
        for number, template in catalogue:
            if number == num_id:
                return number, template
    for number, template in catalogue:
        if template.id.lower() == lab_str.lower():
            return number, template
    clean = lab_str.lower().replace("_", "-")
    for number, template in catalogue:
        if clean in template.id.lower() or template.id.lower() in clean:
            return number, template
    return None, None


def present_template(lab_id: int | str, template: TechnicalLabTemplate, detail: bool = False) -> dict:
    objective = f"Master {template.skill} in practical public administration workflows."
    match = re.search(r"\bdef\s+([a-zA-Z_][a-zA-Z_0-9]*)\s*\(", template.starter_code_template)
    function_name = match.group(1) if match else "process_solution"
    instructions = template.instructions_template.replace("{objective}", objective).replace("{function_name}", function_name)
    public_tests = [
        {"name": item["name"], "description": item.get("description", ""), "test_code": item["test_code"]}
        for item in template.test_cases_template or [] if not item.get("is_hidden")
    ]
    return {
        "id": lab_id,
        "template_id": template.id,
        "title": template.title,
        "objective": objective,
        "language": template.language or "python",
        "difficulty": template.difficulty or "intermediate",
        "status": "validated" if template.test_cases_template else "draft",
        "instructions": instructions,
        "starter_code": template.starter_code_template,
        "constraints": template.constraints or [],
        "test_cases_count": len(template.test_cases_template or []),
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "is_generated": False,
        "tags": template.tags or [],
        **({"test_cases": public_tests, "expected_behavior": "Return outputs satisfying the provided assertions."} if detail else {}),
    }
