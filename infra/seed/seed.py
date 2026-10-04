"""Explicit local catalogue/demo bootstrap; preserves credentials and learner history."""
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, MetaData, Table, create_engine, func, select, text
from sqlalchemy.dialects.postgresql import insert


def seed_schema(schema, tables, url):
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": f"local-seed:{schema}"})
        for name, rows in tables.items():
            table = Table(name, MetaData(), schema=schema, autoload_with=connection)
            inserted = 0
            for source in rows:
                row = dict(source)
                for column in table.columns:
                    if isinstance(column.type, DateTime) and isinstance(row.get(column.name), str):
                        row[column.name] = datetime.fromisoformat(row[column.name])
                # Refuse to attach fixture children to a different existing catalogue.
                key = list(table.primary_key.columns)[0]
                existing = connection.execute(select(table).where(key == row[key.name])).mappings().first()
                if existing:
                    if name == "learner_projections":
                        connection.execute(insert(table).values(**row).on_conflict_do_update(index_elements=[key], set_=row))
                        continue
                    for identity in ("title", "code", "name", "course_id", "module_id", "assessment_id", "domain_id"):
                        if identity in row and existing[identity] != row[identity]:
                            raise RuntimeError(f"Existing {schema}.{name} identifier conflicts with local fixtures; nothing overwritten")
                else:
                    inserted_key = connection.scalar(insert(table).values(**row).on_conflict_do_nothing().returning(key))
                    inserted += int(inserted_key is not None)
            key = list(table.primary_key.columns)[0]
            sequence = connection.scalar(text("SELECT pg_get_serial_sequence(:table, :column)"),
                                         {"table": f"{schema}.{name}", "column": key.name})
            if sequence:
                maximum = connection.scalar(select(func.max(key)))
                if maximum:
                    connection.execute(text("SELECT setval(CAST(:sequence AS regclass), GREATEST(:maximum, pg_sequence_last_value(CAST(:sequence AS regclass))), true)"),
                                       {"sequence": sequence, "maximum": maximum})
            print(f"{schema}.{name}: {inserted} inserted, {len(rows)} catalogue records checked", flush=True)
    engine.dispose()


def seed_demo_accounts():
    """Create only the local login-screen personas; preserve existing credentials."""
    if os.environ.get("DEMO_ACCOUNTS_ENABLED", "true").lower() != "true":
        return []
    engine = create_engine(os.environ["IDENTITY_DATABASE_URL"])
    now = datetime.now().astimezone()
    projections = []
    with engine.begin() as connection:
        users = Table("users", MetaData(), schema="identity", autoload_with=connection)
        profiles = Table("user_profiles", MetaData(), schema="identity", autoload_with=connection)
        personas = [
            (os.environ["DEMO_LEARNER_EMAIL"], os.environ["DEMO_LEARNER_PASSWORD"], "Rajesh Kumar", "learner", True, "Senior Statistical Officer (SSO)"),
            (os.environ["DEMO_ADMIN_EMAIL"], os.environ["DEMO_ADMIN_PASSWORD"], "Director General Admin", "admin", True, "Director General"),
            (os.environ["DEMO_NEW_OFFICER_EMAIL"], os.environ["DEMO_NEW_OFFICER_PASSWORD"], "Priya Sharma", "learner", False, ""),
        ]
        for email, password, name, role, onboarded, designation in personas:
            if not password:
                raise RuntimeError("Enabled local demo account requires a configured development password")
            user = connection.execute(select(users).where(users.c.email == email)).mappings().first()
            if not user:
                salt = os.urandom(16).hex()
                digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
                user_id = connection.scalar(insert(users).values(email=email, password_hash=f"{salt}${digest}",
                    full_name=name, role=role, is_active=True, created_at=now, updated_at=now).returning(users.c.id))
            else:
                user_id = user["id"]
            profile = connection.execute(select(profiles).where(profiles.c.user_id == user_id)).mappings().first()
            if not profile:
                connection.execute(insert(profiles).values(user_id=user_id, work_experience_years=0,
                    designation=designation, department="MoSPI" if onboarded else "", language_pref="en", appearance_pref="light",
                    onboarding_completed=onboarded, daily_goal_minutes=30, current_streak_days=1,
                    last_active_date=now, created_at=now, updated_at=now))
        # Refresh read-model snapshots using the identity role, then write through
        # the learning role. This is local bootstrap tooling, not a service query.
        rows = connection.execute(select(users.c.id, users.c.email, users.c.full_name, users.c.role,
            profiles.c.designation, profiles.c.department, profiles.c.onboarding_completed,
            profiles.c.daily_goal_minutes, profiles.c.current_streak_days, profiles.c.last_active_date)
            .join(profiles, profiles.c.user_id == users.c.id)).mappings()
        for row in rows:
            data = dict(row)
            data["user_id"] = data.pop("id")
            data["updated_at"] = now
            projections.append(data)
    engine.dispose()
    print("Local demo personas checked; existing accounts and credentials preserved", flush=True)
    return projections


def main():
    if os.environ.get("LOCAL_DEMO_SEED_ENABLED", "true").lower() != "true":
        print("Local catalogue bootstrap disabled", flush=True)
        return
    fixtures = json.loads(Path(__file__).with_name("catalogue.json").read_text(encoding="utf-8"))
    projections = seed_demo_accounts()
    if projections:
        fixtures["learning"]["learner_projections"] = projections
    for schema, tables in fixtures.items():
        seed_schema(schema, tables, os.environ[f"{schema.upper()}_DATABASE_URL"])


if __name__ == "__main__":
    main()
