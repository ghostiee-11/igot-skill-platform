"""Dry-run-first migration from the monolith database into service schemas.

The command never reads the repository's .env. Dry-run needs only --source-url.
Applying additionally requires --target-url and --apply. Existing destination
rows are not overwritten; unmapped tables/fields are retained in the migration
archive so reconciliation can report rather than discard them.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy import MetaData, Table, create_engine, func, inspect, select, text
from sqlalchemy.exc import IntegrityError


@dataclass(frozen=True)
class Destination:
    schema: str
    table: str
    transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _question(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "assessment_id": row["assessment_id"],
        "text": row["text"],
        "options": _json(row.get("options_json"), []),
        "correct_option_index": row["correct_option_index"],
        "explanation": row.get("explanation") or "",
        "order": row.get("order", 0),
    }


def _attempt(row: dict[str, Any]) -> dict[str, Any]:
    result = {
        "attempt_id": str(row["id"]),
        "score_percent": row["score_percent"],
        "passed": row["passed"],
        "breakdown": [],
        "legacy_import": True,
    }
    return {
        "id": str(row["id"]),
        "user_id": row["user_id"],
        "assessment_id": row["assessment_id"],
        "engine": "course_quiz",
        "score_percent": row["score_percent"],
        "passed": row["passed"],
        "answers": _json(row.get("answers_json"), {}),
        "result": result,
        "submitted_at": row.get("submitted_at"),
    }


def _assessment(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "engine": "course_quiz", "metadata_json": {}}


def _transcript(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["chunks_json"] = _json(row.get("chunks_json"), [])
    row["metadata_json"] = _json(row.get("metadata_json"), {})
    return row


def _json_fields(**field_map: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a transform that decodes legacy JSON text into typed columns."""
    def transform(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        for source, destination in field_map.items():
            value = result.pop(source, None)
            fallback: Any = {} if destination in {
                "parameters", "options_map", "artifacts_spec", "artifacts", "chart"
            } else []
            result[destination] = _json(value, fallback)
        return result

    return transform


DESTINATIONS: dict[str, tuple[Destination, ...]] = {
    "users": (Destination("identity", "users"),),
    "user_profiles": (Destination("identity", "user_profiles"),),
    "departments": (Destination("identity", "departments"),),
    "courses": (Destination("learning", "courses"),),
    "modules": (Destination("learning", "modules"),),
    "lessons": (Destination("learning", "lessons"),),
    "skills": (Destination("competency", "skills"), Destination("learning", "skills")),
    "course_skills": (Destination("learning", "course_skills"),),
    "user_skills": (Destination("competency", "user_skills"),),
    "enrollments": (Destination("learning", "enrollments"),),
    "progress_records": (Destination("learning", "progress_records"),),
    "planned_courses": (Destination("learning", "planned_courses"),),
    "learning_history": (Destination("learning", "learning_history"),),
    "search_history": (Destination("learning", "search_history"),),
    "assessments": (Destination("assessment", "assessments", _assessment),),
    "questions": (Destination("assessment", "questions", _question),),
    "assessment_attempts": (Destination("assessment", "attempts", _attempt),),
    "generated_quizzes": (Destination("assessment", "generated_quizzes"),),
    "generated_quiz_questions": (Destination(
        "assessment", "generated_quiz_questions",
        _json_fields(options_json="options"),
    ),),
    "quiz_attempts": (Destination(
        "assessment", "quiz_attempts",
        _json_fields(answers_json="answers"),
    ),),
    "stat_engine_questions": (Destination(
        "assessment", "stat_engine_questions",
        _json_fields(
            parameters_json="parameters", correct_answer_json="correct_answer",
            options_map_json="options_map", chart_json="chart",
        ),
    ),),
    "technical_lab_templates": (Destination(
        "assessment", "technical_lab_templates",
        _json_fields(
            tags_json="tags", constraints_json="constraints",
            test_cases_template_json="test_cases_template",
        ),
    ),),
    "cyber_sandbox_templates": (Destination(
        "assessment", "cyber_sandbox_templates",
        _json_fields(
            tags_json="tags", mitre_techniques_json="mitre_techniques",
            hints_template_json="hints_template", artifacts_spec_json="artifacts_spec",
        ),
    ),),
    "cyber_sandbox_challenges": (Destination(
        "assessment", "cyber_sandbox_challenges",
        _json_fields(
            tags_json="tags", mitre_techniques_json="mitre_techniques",
            objectives_json="objectives", hints_json="hints", artifacts_json="artifacts",
        ),
    ),),
    "cyber_sandbox_sessions": (Destination(
        "labs", "legacy_cyber_sessions",
        _json_fields(unlocked_hints_json="unlocked_hints"),
    ),),
    "competency_domains": (Destination("competency", "competency_domains"),),
    "competencies": (Destination("competency", "competencies"),),
    "competency_profiles": (Destination("competency", "competency_profiles"),),
    "user_competency_scores": (Destination("competency", "user_competency_scores"),),
    "gap_analyses": (Destination("competency", "gap_analyses"),),
    "recommendations": (Destination("competency", "recommendations"),),
    "evidence_competency_mapping": (Destination("competency", "evidence_competency_mapping"),),
    "user_cyber_competencies": (Destination("competency", "user_cyber_competencies"),),
    "technical_transcripts": (Destination("content", "technical_transcripts", _transcript),),
}

# These records do not yet have a behaviorally equivalent typed destination.
# They are archived losslessly during apply and remain migration blockers.
ARCHIVE_TABLES = {
    "stat_engine_attempts", "stat_engine_mastery",
    "behavioural_session_results", "technical_learning_objectives",
    "technical_generated_labs", "technical_lab_solutions",
    "technical_lab_validation_results",
}

# Parent rows must exist before children because service schemas retain their
# internal foreign keys. Tables omitted here are processed afterwards.
TABLE_ORDER = [
    "departments", "users", "user_profiles",
    "courses", "skills", "modules", "lessons", "course_skills",
    "enrollments", "progress_records", "planned_courses", "learning_history", "search_history",
    "competency_domains", "competencies", "competency_profiles", "user_competency_scores",
    "gap_analyses", "recommendations", "evidence_competency_mapping", "user_cyber_competencies", "user_skills",
    "assessments", "questions", "assessment_attempts",
    "generated_quizzes", "generated_quiz_questions", "quiz_attempts",
    "stat_engine_questions", "technical_lab_templates",
    "cyber_sandbox_templates", "cyber_sandbox_challenges", "cyber_sandbox_sessions",
    "technical_transcripts",
]


def inventory(source_engine) -> dict[str, Any]:
    inspector = inspect(source_engine)
    rows: dict[str, Any] = {}
    with source_engine.connect() as connection:
        for table_name in inspector.get_table_names():
            table = Table(table_name, MetaData(), autoload_with=source_engine)
            count = connection.execute(select(text("count(*)")).select_from(table)).scalar_one()
            if table_name in DESTINATIONS:
                state = "mapped"
            elif table_name in ARCHIVE_TABLES:
                state = "archive_pending_typed_migration"
            elif table_name.startswith("alembic_"):
                state = "migration_metadata"
            else:
                state = "unmapped"
            rows[table_name] = {"rows": count, "state": state}
    return rows


def _serializable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return {"encoding": "hex", "value": value.hex()}
    return value


def _primary_key(inspector, table_name: str, row: dict[str, Any]) -> str:
    columns = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
    if columns:
        return "|".join(str(row.get(column)) for column in columns)
    return str(row.get("id", "unknown"))


def _prepare_archive(target) -> None:
    target.execute(text("CREATE SCHEMA IF NOT EXISTS migration"))
    target.execute(text("""
        CREATE TABLE IF NOT EXISTS migration.legacy_records (
            source_table text NOT NULL,
            source_key text NOT NULL,
            payload jsonb NOT NULL,
            imported_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (source_table, source_key)
        )
    """))


def apply(source_engine, target_engine) -> dict[str, Any]:
    source_inspector = inspect(source_engine)
    report = {"inserted": {}, "archived": {}, "skipped_existing": {}, "failed": {}, "errors": {}, "sequences": {}}
    source_metadata = MetaData()
    target_metadata = MetaData()
    with source_engine.connect() as source, target_engine.begin() as target:
        _prepare_archive(target)
        available_target = set(inspect(target).get_schema_names())
        source_tables = source_inspector.get_table_names()
        rank = {name: index for index, name in enumerate(TABLE_ORDER)}
        for table_name in sorted(source_tables, key=lambda name: (rank.get(name, len(rank)), name)):
            source_table = Table(table_name, source_metadata, autoload_with=source_engine)
            rows = [dict(row) for row in source.execute(select(source_table)).mappings()]
            destinations = DESTINATIONS.get(table_name, ())
            for destination in destinations:
                if destination.schema not in available_target:
                    raise RuntimeError(f"target schema missing: {destination.schema}")
                target_table = Table(destination.table, target_metadata, schema=destination.schema, autoload_with=target)
                allowed = set(target_table.c.keys())
                inserted = skipped = failed = 0
                for row in rows:
                    transformed = destination.transform(row) if destination.transform else dict(row)
                    payload = {key: value for key, value in transformed.items() if key in allowed}
                    if not payload:
                        continue
                    try:
                        with target.begin_nested():
                            target.execute(target_table.insert().values(**payload))
                        inserted += 1
                    except IntegrityError as exc:
                        if getattr(exc.orig, "sqlstate", None) == "23505":
                            skipped += 1
                        else:
                            failed += 1
                            report["errors"].setdefault(f"{destination.schema}.{destination.table}", str(exc.orig).splitlines()[0])
                    except Exception as exc:
                        failed += 1
                        report["errors"].setdefault(f"{destination.schema}.{destination.table}", f"{type(exc).__name__}: {exc}")
                key = f"{destination.schema}.{destination.table}"
                report["inserted"][key] = report["inserted"].get(key, 0) + inserted
                report["skipped_existing"][key] = report["skipped_existing"].get(key, 0) + skipped
                report["failed"][key] = report["failed"].get(key, 0) + failed

            if table_name in ARCHIVE_TABLES or not destinations:
                archived = 0
                for row in rows:
                    source_key = _primary_key(source_inspector, table_name, row)
                    payload = json.dumps({key: _serializable(value) for key, value in row.items()})
                    result = target.execute(
                        text("""
                            INSERT INTO migration.legacy_records(source_table, source_key, payload)
                            VALUES (:table, :key, CAST(:payload AS jsonb))
                            ON CONFLICT (source_table, source_key) DO NOTHING
                        """),
                        {"table": table_name, "key": source_key, "payload": payload},
                    )
                    archived += result.rowcount
                report["archived"][table_name] = archived
        if target_engine.dialect.name == "postgresql":
            seen: set[tuple[str, str]] = set()
            for destinations in DESTINATIONS.values():
                for destination in destinations:
                    key = (destination.schema, destination.table)
                    if key in seen:
                        continue
                    seen.add(key)
                    table = Table(destination.table, MetaData(), schema=destination.schema, autoload_with=target)
                    primary_keys = list(table.primary_key.columns)
                    if len(primary_keys) != 1:
                        continue
                    column = primary_keys[0]
                    sequence = target.execute(
                        text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
                        {"table_name": f"{destination.schema}.{destination.table}", "column_name": column.name},
                    ).scalar_one()
                    if not sequence:
                        continue
                    maximum = target.execute(select(func.max(column))).scalar_one()
                    target.execute(
                        text("SELECT setval(CAST(:sequence AS regclass), :value, :called)"),
                        {"sequence": sequence, "value": maximum or 1, "called": maximum is not None},
                    )
                    report["sequences"][f"{destination.schema}.{destination.table}.{column.name}"] = maximum
    return report


def reconcile_counts(source_engine, target_engine) -> dict[str, dict[str, Any]]:
    """Compare every mapped source count with each typed destination count."""
    report: dict[str, dict[str, Any]] = {}
    source_metadata = MetaData()
    target_metadata = MetaData()
    with source_engine.connect() as source, target_engine.connect() as target:
        for source_name, destinations in DESTINATIONS.items():
            source_table = Table(source_name, source_metadata, autoload_with=source)
            expected = source.execute(select(text("count(*)")).select_from(source_table)).scalar_one()
            for destination in destinations:
                target_table = Table(destination.table, target_metadata, schema=destination.schema, autoload_with=target)
                actual = target.execute(select(text("count(*)")).select_from(target_table)).scalar_one()
                report[f"{source_name}->{destination.schema}.{destination.table}"] = {
                    "expected": expected, "actual": actual, "matches": expected == actual,
                }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--target-url")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.target_url:
        parser.error("--target-url is required with --apply")
    source_engine = create_engine(args.source_url)
    result = inventory(source_engine)
    print(json.dumps({"mode": "apply" if args.apply else "dry-run", "inventory": result}, indent=2))
    blockers = [name for name, item in result.items() if item["state"] in {"unmapped", "archive_pending_typed_migration"} and item["rows"]]
    if args.apply:
        target_engine = create_engine(args.target_url)
        migration_report = apply(source_engine, target_engine)
        print(json.dumps({"migration": migration_report}, indent=2))
        if any(migration_report["failed"].values()):
            return 3
        reconciliation = reconcile_counts(source_engine, target_engine)
        print(json.dumps({"reconciliation": reconciliation}, indent=2))
        if not all(item["matches"] for item in reconciliation.values()):
            return 4
    if blockers:
        print(json.dumps({"typed_migration_blockers": blockers}, indent=2))
    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
