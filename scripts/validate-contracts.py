"""Perform dependency-free structural checks on exported API and event contracts."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    errors: list[str] = []
    for path in sorted(Path("contracts/events").glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        required = set(schema.get("required", []))
        expected = {"event_id", "event_type", "schema_version", "occurred_at", "producer", "idempotency_key", "data"}
        if not expected.issubset(required):
            errors.append(f"{path}: missing envelope requirements {sorted(expected - required)}")
        if schema.get("additionalProperties") is not False:
            errors.append(f"{path}: top-level event envelope must reject unknown fields")

    for path in sorted(Path("contracts/http").glob("*.openapi.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        if not str(spec.get("openapi", "")).startswith("3."):
            errors.append(f"{path}: expected an OpenAPI 3 document")
        if not isinstance(spec.get("paths"), dict):
            errors.append(f"{path}: paths must be an object")

    if errors:
        print("\n".join(errors))
        return 1
    event_count = len(list(Path("contracts/events").glob("*.schema.json")))
    api_count = len(list(Path("contracts/http").glob("*.openapi.json")))
    print(f"validated {event_count} event schemas and {api_count} exported API contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
