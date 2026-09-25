"""Export the monolith's authored tabletop scenarios without importing its runtime."""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend/app/modules/digital_governance"
TARGET = ROOT / "services/assessment/src/igot_assessment/scenarios.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


for package in ("app", "app.modules", "app.modules.digital_governance", "app.modules.digital_governance.services"):
    sys.modules[package] = ModuleType(package)

load("app.modules.digital_governance.schemas", SOURCE / "schemas.py")
service = load("app.modules.digital_governance.services.scenario_service", SOURCE / "services/scenario_service.py")
service.ScenarioRepository.initialize_scenarios()
scenarios = [scenario.model_dump(mode="json") for scenario in service.ScenarioRepository._scenarios.values()]
TARGET.write_text(json.dumps(scenarios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Exported {len(scenarios)} scenarios and {sum(len(item['questions']) for item in scenarios)} questions")
