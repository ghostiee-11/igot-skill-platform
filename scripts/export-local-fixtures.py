"""Export authored rebuild/lms content for fresh local Compose databases.

This development export reads the historical seed source without executing its
database seed. Runtime services consume the resulting JSON, never backend imports.
Run with the assessment service's Python environment from the repository root.
"""
import ast
import base64
import importlib
import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tree(path):
    return ast.parse((ROOT / path).read_text(encoding="utf-8"))


def literal(node, names=None):
    names = names or {}
    if isinstance(node, ast.Name):
        return names[node.id]
    if isinstance(node, ast.Attribute) and node.attr == "id":
        return names[node.value.id]["id"]
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal(x, names) for x in node.elts]
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute) and ast.unparse(node.func) == "json.dumps":
            return json.dumps(literal(node.args[0], names), ensure_ascii=False)
        if isinstance(node.func, ast.Name) and node.func.id in {"LabTemplateSchema", "TestCaseSchema"}:
            return {k.arg: literal(k.value, names) for k in node.keywords}
    return ast.literal_eval(node)


def function(module, name):
    return next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)


def constructor_assignments(fn):
    return sorted((n for n in ast.walk(fn) if isinstance(n, ast.Assign)
                   and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                   and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)),
                  key=lambda n: n.lineno)


def export():
    seed = tree("backend/app/core/seed_data.py")
    digital = tree("backend/app/modules/digital_governance/seed_data.py")
    names = {}
    courses = []
    assessments = []
    questions = []
    for n in constructor_assignments(function(seed, "seed_database")):
        if n.value.func.id == "Course":
            row = {k.arg: literal(k.value, names) for k in n.value.keywords}
            row["id"] = len(courses) + 1
            row["created_at"] = "2026-09-25T00:00:00+00:00"
            courses.append(row)
            names[n.targets[0].id] = row
    fn = function(digital, "seed_digital_governance_curriculum")
    title = next(n.value for n in fn.body if isinstance(n, ast.Assign)
                 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "course_title")
    names["course_title"] = literal(title)
    call = next(n.value for n in constructor_assignments(fn) if n.value.func.id == "Course")
    row = {k.arg: literal(k.value, names) for k in call.keywords}
    row.update(id=4, created_at="2026-09-25T00:00:00+00:00")
    courses.append(row)
    names["c4"] = names["course"] = row

    modules, lessons = [], []
    for n in constructor_assignments(function(seed, "sync_course_curriculum_videos")):
        kind = n.value.func.id
        if kind not in {"Module", "Lesson"}:
            continue
        row = {k.arg: literal(k.value, names) for k in n.value.keywords}
        if kind == "Lesson":
            for key in ("video_start_time", "video_end_time", "source_video_title", "topic", "learning_objective"):
                row.pop(key, None)
        target = modules if kind == "Module" else lessons
        row["id"] = len(target) + 1
        target.append(row)
        names[n.targets[0].id] = row

    for n in constructor_assignments(function(seed, "seed_database")):
        kind = n.value.func.id
        if kind not in {"Assessment", "Question"}:
            continue
        row = {k.arg: literal(k.value, names) for k in n.value.keywords}
        target = assessments if kind == "Assessment" else questions
        row["id"] = len(target) + 1
        if kind == "Assessment":
            row.update(engine="course_quiz", metadata_json={})
        else:
            row["options"] = json.loads(row.pop("options_json"))
        target.append(row)
        names[n.targets[0].id] = row
    call = next(n.value for n in constructor_assignments(fn) if n.value.func.id == "Assessment")
    exam = {k.arg: literal(k.value, names) for k in call.keywords}
    exam.update(id=3, engine="course_quiz", metadata_json={})
    assessments.append(exam)
    data = next(n.value for n in fn.body if isinstance(n, ast.Assign)
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "questions_data")
    for order, (text, options, answer, explanation) in enumerate(literal(data), 1):
        questions.append(dict(id=len(questions)+1, assessment_id=3, text=text,
                              options=options, correct_option_index=answer,
                              explanation=explanation, order=order))
    for exam in assessments:
        courses[exam["course_id"]-1]["assessment_id"] = exam["id"]

    constants = {n.targets[0].id: literal(n.value) for n in tree("backend/app/core/seed_competencies.py").body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id.isupper()}
    domains, competencies, skills, links, mappings = [], [], [], [], []
    code_ids = {}
    for domain_id, (code, name, description) in enumerate(constants["DOMAINS"], 1):
        domains.append(dict(id=domain_id, code=code, name=name, description=description))
        for competency_code, competency_name in constants["COMPETENCIES"][code]:
            comp_id = len(competencies)+1
            code_ids[competency_code] = comp_id
            competencies.append(dict(id=comp_id, domain_id=domain_id, code=competency_code,
                                     name=competency_name, max_level=5))
    # Course skills are the authored course outcomes, not every competency in
    # the domain taxonomy. Keep their identifiers distinct from taxonomy IDs.
    core_skills = next(n.value for n in function(seed, "seed_database").body
                       if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                       and n.targets[0].id == "skills_data")
    gov_skills = next(n.value for n in fn.body if isinstance(n, ast.Assign)
                      and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "gov_skills")
    for index, (name, category) in enumerate(literal(core_skills) + literal(gov_skills), 1):
        skill_id = 100 + index
        skills.append(dict(id=skill_id, name=name, category=category))
        links.append(dict(id=skill_id, course_id=index if index <= 4 else 4, skill_id=skill_id))
    for system, key in (("stat_engine_skill", "STAT_ENGINE_SKILL_TO_COMPETENCY_CODE"),
                        ("stat_engine_competency", "STAT_ENGINE_COMPETENCY_TO_COMPETENCY_CODE"),
                        ("behavioural_competency", "BEHAVIOURAL_NAME_TO_COMPETENCY_CODE")):
        for source_key, code in constants[key].items():
            mappings.append(dict(id=len(mappings)+1, source_system=system,
                                 source_key=source_key, competency_id=code_ids[code]))
    templates = tree("backend/app/modules/technical_courses/services/template_service.py")
    template_data = next(n.value for n in templates.body if isinstance(n, ast.AnnAssign)
                         and n.target.id == "BUILTIN_LAB_TEMPLATES")
    labs = literal(template_data)
    for lab in labs:
        lab["created_at"] = "2026-09-25T00:00:00+00:00"

    # Import only pure content generators; bypass legacy package initializers that
    # import database models. This exporter never imports app.core.database.
    sys.path.insert(0, str(ROOT / "backend"))
    for package in ("app.modules", "app.modules.digital_governance", "app.modules.digital_governance.services"):
        module = types.ModuleType(package)
        module.__path__ = [str(ROOT / "backend" / package.replace(".", "/"))]
        sys.modules[package] = module
    registry = importlib.import_module("app.modules.digital_governance.services.templates")
    cyber = []
    for challenge_id in ("01-soc-auth-investigation", "03-compromised-linux-server", "04-vulnerable-web-app",
                         "05-threat-hunting-lotl", "06-pki-token-dispute", "07-meghraj-cloud-audit"):
        template = registry.get_template(challenge_id)
        slots = template.generate_random_slots(seed=f"official_seed_{challenge_id}")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            files = template.synthesize_artifacts(slots, path)
            notebook = template.generate_notebook(slots, path)
            artifacts = {}
            for name, artifact in files.items():
                try:
                    artifacts[name] = artifact.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    artifacts[name] = "base64:" + base64.b64encode(artifact.read_bytes()).decode("ascii")
            cyber.append(dict(id=challenge_id, template_id=template.template_id, title=template.title,
                              category=template.category, difficulty=template.difficulty, points=template.base_points,
                              duration_minutes=template.duration_minutes, competency_id=template.competency_id,
                              is_flagship=False, tags=template.tags, mitre_techniques=template.mitre_techniques,
                              objectives=template.generate_objectives(slots), scenario_markdown=template.generate_scenario_description(slots),
                              flag=template.compute_flag(slots), hints=template.generate_hints(slots), artifacts=artifacts,
                              notebook_code=notebook.read_text(encoding="utf-8"), created_at="2026-09-25T00:00:00+00:00"))
    generator_module = importlib.import_module("app.statistical_engine.questions.generator")
    generator = generator_module.QuestionGenerator()
    stat_questions = []
    for index, template in enumerate(generator._templates_cache.values()):
        _, internal = generator.generate_question(template["skill_id"], question_type=generator_module.QuestionType(template["type"]),
                                                   difficulty=generator_module.QuestionDifficulty(template["difficulty"]), seed=100+index)
        data = internal.to_dict()
        data["question_id"] = f"local-{template['template_id']}"
        data["created_at"] = "2026-09-25T00:00:00+00:00"
        stat_questions.append(data)
    fixture = {
        "learning": {"courses":courses, "modules":modules, "lessons":lessons, "skills":skills, "course_skills":links},
        "assessment": {"assessments":assessments, "questions":questions, "technical_lab_templates":labs,
                       "cyber_sandbox_challenges":cyber, "stat_engine_questions":stat_questions},
        "competency": {"competency_domains":domains, "competencies":competencies, "skills":skills,
                       "evidence_competency_mapping":mappings,
                       "course_candidates":[dict(course_id=c["id"], title=c["title"], category=c["category"],
                                                 difficulty=c["difficulty"], overview=c["overview"], updated_at=c["created_at"]) for c in courses]},
    }
    output = ROOT / "infra/seed/catalogue.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(fixture, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print({schema:{table:len(rows) for table,rows in tables.items()} for schema,tables in fixture.items()})


if __name__ == "__main__":
    export()
