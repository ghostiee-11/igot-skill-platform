"""Authored digital-governance scenarios and durable session transitions."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache
def catalogue() -> dict[str, dict[str, Any]]:
    path = Path(__file__).with_name("scenarios.json")
    return {item["id"]: item for item in json.loads(path.read_text(encoding="utf-8"))}


def summaries() -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "domain": item["domain"],
            "ministry": item["ministry"],
            "statutory_framework": item["statutory_framework"],
            "difficulty": item["difficulty"],
            "estimated_minutes": item["estimated_minutes"],
            "summary": item["initial_context"][:180] + "...",
            "objectives_count": len(item["learning_objectives"]),
        }
        for item in catalogue().values()
    ]


def start(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": scenario["id"],
        "current_question_id": scenario["root_question_id"],
        "compliance_score": 50,
        "step_number": 1,
        "optimal_count": 0,
        "total_steps": 0,
        "is_terminal": False,
        "decision_trail": [],
    }


def start_response(session_id: str, scenario: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "scenario_id": scenario["id"],
        "scenario_title": scenario["title"],
        "domain": scenario["domain"],
        "ministry": scenario["ministry"],
        "initial_context": scenario["initial_context"],
        "statutory_framework": scenario["statutory_framework"],
        "current_question": scenario["questions"][state["current_question_id"]],
        "compliance_score": state["compliance_score"],
        "step_number": state["step_number"],
    }


def summary(session_id: str, scenario: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    score = state["compliance_score"]
    resolved = score >= 70
    return {
        "session_id": session_id,
        "scenario_id": scenario["id"],
        "scenario_title": scenario["title"],
        "domain": scenario["domain"],
        "ministry": scenario["ministry"],
        "total_steps": state["total_steps"],
        "optimal_steps": state["optimal_count"],
        "procedural_compliance_score": score,
        "resolved_satisfactorily": resolved,
        "decision_trail": state["decision_trail"],
        "key_regulatory_takeaways": [
            f"Compliance Framework: {', '.join(scenario['statutory_framework'])}",
            f"Procedural Compliance: {score}% ({'Pass Standard Achieved' if resolved else 'Procedural Deficiencies Noted'})",
            f"Optimal Incident Decisions: {state['optimal_count']} of {state['total_steps']} decision checkpoints",
            f"Institutional Stakeholder: {scenario['ministry']}",
        ],
    }


def answer(session_id: str, scenario: dict[str, Any], state: dict[str, Any], option_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if state["is_terminal"]:
        raise ValueError("Scenario session is complete")
    question = scenario["questions"][state["current_question_id"]]
    option = next((item for item in question["options"] if item["option_id"] == option_id), None)
    if option is None:
        raise ValueError("Option does not belong to the current question")
    next_state = {**state, "decision_trail": list(state["decision_trail"])}
    next_state["step_number"] += 1
    next_state["total_steps"] += 1
    next_state["optimal_count"] += int(option["is_optimal"])
    next_state["compliance_score"] = max(0, min(100, next_state["compliance_score"] + option["compliance_delta"]))
    next_state["decision_trail"].append({
        "step": next_state["total_steps"],
        "stage_title": question["stage_title"],
        "question_prompt": question["prompt"],
        "selected_option_id": option["option_id"],
        "selected_option_text": option["text"],
        "is_optimal": option["is_optimal"],
        "consequence_summary": option["consequence_summary"],
        "statutory_rationale": option["statutory_rationale"],
        "score_after_decision": next_state["compliance_score"],
    })
    next_question = scenario["questions"].get(option.get("next_question_id"))
    terminal = bool(option["is_terminal"] or next_question is None)
    next_state["is_terminal"] = terminal
    if next_question is not None and not terminal:
        next_state["current_question_id"] = next_question["id"]
    response = {
        "session_id": session_id,
        "is_terminal": terminal,
        "selected_option": option,
        "next_question": None if terminal else next_question,
        "compliance_score": next_state["compliance_score"],
        "step_number": next_state["step_number"],
        "session_summary": summary(session_id, scenario, next_state) if terminal else None,
    }
    return next_state, response
