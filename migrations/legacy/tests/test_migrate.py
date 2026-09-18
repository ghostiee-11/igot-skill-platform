from sqlalchemy import create_engine, text

from migrate import DESTINATIONS, _attempt, _json_fields, _question, inventory, reconcile_counts


def test_inventory_reports_mapped_archive_and_unmapped_tables():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users(id integer primary key, email text)"))
        connection.execute(text("INSERT INTO users VALUES (1, 'a@example.gov.in')"))
        connection.execute(text("CREATE TABLE stat_engine_mastery(id integer primary key)"))
        connection.execute(text("CREATE TABLE mystery(id integer primary key)"))
    result = inventory(engine)
    assert result["users"] == {"rows": 1, "state": "mapped"}
    assert result["stat_engine_mastery"]["state"] == "archive_pending_typed_migration"
    assert result["mystery"]["state"] == "unmapped"


def test_assessment_transforms_preserve_legacy_identifiers_and_json():
    question = _question({
        "id": 4, "assessment_id": 2, "text": "Q", "options_json": '["A", "B"]',
        "correct_option_index": 1, "explanation": "Because", "order": 3,
    })
    assert question["id"] == 4 and question["options"] == ["A", "B"]
    attempt = _attempt({
        "id": 9, "user_id": 1, "assessment_id": 2, "score_percent": 80,
        "passed": True, "answers_json": '{"4": 1}', "submitted_at": None,
    })
    assert attempt["id"] == "9"
    assert attempt["answers"] == {"4": 1}


def test_specialist_tables_have_typed_destinations_and_decode_json():
    expected = {
        "generated_quizzes", "generated_quiz_questions", "stat_engine_questions",
        "technical_lab_templates", "cyber_sandbox_templates",
        "cyber_sandbox_challenges", "cyber_sandbox_sessions",
    }
    assert expected <= DESTINATIONS.keys()

    transform = _json_fields(tags_json="tags", artifacts_json="artifacts")
    result = transform({"id": "challenge-1", "tags_json": '["iam"]', "artifacts_json": '{"file":"a"}'})
    assert result == {"id": "challenge-1", "tags": ["iam"], "artifacts": {"file": "a"}}


def test_populated_specialist_table_is_mapped_not_a_blocker():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE cyber_sandbox_challenges(id text primary key)"))
        connection.execute(text("INSERT INTO cyber_sandbox_challenges VALUES ('one')"))
    assert inventory(engine)["cyber_sandbox_challenges"] == {"rows": 1, "state": "mapped"}


def test_count_reconciliation_reports_mismatch():
    source = create_engine("sqlite://")
    target = create_engine("sqlite://")
    with source.begin() as connection:
        connection.execute(text("CREATE TABLE users(id integer primary key, email text)"))
        connection.execute(text("INSERT INTO users VALUES (1, 'a@example.gov.in')"))
    with target.begin() as connection:
        connection.execute(text("CREATE TABLE users(id integer primary key, email text)"))
    original = dict(DESTINATIONS)
    try:
        DESTINATIONS.clear()
        from migrate import Destination
        DESTINATIONS["users"] = (Destination(None, "users"),)
        result = reconcile_counts(source, target)
        assert result["users->None.users"] == {"expected": 1, "actual": 0, "matches": False}
    finally:
        DESTINATIONS.clear()
        DESTINATIONS.update(original)
