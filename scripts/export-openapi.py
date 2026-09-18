"""Export live service OpenAPI documents into the contracts directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_SERVICES = {
    "gateway": "http://localhost:8000",
    "identity": "http://localhost:8101",
    "learning": "http://localhost:8102",
    "assessment": "http://localhost:8103",
    "competency": "http://localhost:8104",
    "ai": "http://localhost:8105",
    "content": "http://localhost:8106",
    "labs": "http://localhost:8107",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("contracts/http"))
    parser.add_argument("--service", action="append", choices=sorted(DEFAULT_SERVICES))
    args = parser.parse_args()

    selected = args.service or list(DEFAULT_SERVICES)
    args.output.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []
    for name in selected:
        url = f"{DEFAULT_SERVICES[name]}/openapi.json"
        try:
            with urlopen(url, timeout=10) as response:  # noqa: S310 - fixed local service URLs
                document = json.load(response)
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"{name}: unable to export {url}: {exc}")
            failed.append(name)
            continue
        destination = args.output / f"{name}.openapi.json"
        destination.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{name}: {destination}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
