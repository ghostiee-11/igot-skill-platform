from __future__ import annotations

from typing import Any


COMPETENCIES = [
    "Course Knowledge",
    "Communication",
    "Decision Making",
    "Leadership",
    "Ethical Reasoning",
    "Planning and Coordination",
    "Change Management",
]

PHASES = [
    ("Course understanding", "Course Knowledge"),
    ("Applied communication", "Communication"),
    ("Decision scenario", "Decision Making"),
    ("Leadership scenario", "Leadership"),
    ("Ethics and public service", "Ethical Reasoning"),
    ("Implementation and change", "Change Management"),
]

KEYWORDS = {
    "Course Knowledge": ("course", "module", "framework", "policy", "data", "evidence"),
    "Communication": ("communicate", "listen", "explain", "stakeholder", "feedback"),
    "Decision Making": ("decide", "option", "risk", "evidence", "trade-off", "priority"),
    "Leadership": ("lead", "team", "delegate", "mentor", "accountability"),
    "Ethical Reasoning": ("ethical", "integrity", "fair", "transparent", "public interest"),
    "Planning and Coordination": ("plan", "coordinate", "timeline", "milestone", "resource"),
    "Change Management": ("change", "adoption", "resistance", "transition", "training"),
}


def _question(index: int, state: dict[str, Any]) -> str:
    name = state["officer_name"]
    title = state["course_title"]
    questions = [
        f"Good morning, {name}. What is the most useful idea you took from {title}, and where would you apply it in your work?",
        "Describe how you would explain that idea to colleagues who have different levels of technical knowledge.",
        "Suppose the available evidence is incomplete but a decision is urgent. How would you proceed, and what safeguards would you use?",
        "Tell the board about a difficult team situation you would need to lead through. What would you do first, and why?",
        "Imagine that a senior colleague asks you to bypass a required process to save time. How would you respond?",
        "How would you turn your proposed approach into an implementation plan and help people adopt the change?",
    ]
    if index < len(questions):
        return questions[index]
    return f"Thank you, {name}. That concludes the interview. Your assessment report is being prepared."


def start_state(course_id: int, course_title: str, officer_name: str, duration: int) -> dict[str, Any]:
    state = {
        "course_id": course_id,
        "course_title": course_title,
        "officer_name": officer_name,
        "target_duration_minutes": duration,
        "turns": [],
        "transcript": [],
    }
    opening = _question(0, state)
    state["transcript"] = [{
        "speaker": "AI Interviewer",
        "content": opening,
        "timestamp_seconds": 0,
        "behavioral_tags": [PHASES[0][1]],
    }]
    return state


def tags_for(text: str) -> list[str]:
    lower = text.lower()
    return [name for name, words in KEYWORDS.items() if any(word in lower for word in words)]


def submit_turn(state: dict[str, Any], officer_response: str, elapsed_seconds: int, metrics: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    state = {**state, "turns": list(state.get("turns", [])), "transcript": list(state.get("transcript", []))}
    answer_number = len(state["turns"]) + 1
    if answer_number > len(PHASES):
        raise ValueError("The interview has already received all answers")
    clean_text = officer_response.strip()
    if not clean_text:
        raise ValueError("An interview answer cannot be empty")
    tags = tags_for(clean_text)
    state["transcript"].append({
        "speaker": f"Officer {state['officer_name']}",
        "content": clean_text,
        "timestamp_seconds": elapsed_seconds,
        "behavioral_tags": tags,
    })
    state["turns"].append({
        "turn": answer_number,
        "response": clean_text,
        "elapsed_seconds": elapsed_seconds,
        "metrics": {key: value for key, value in metrics.items() if value is not None},
        "tags": tags,
    })
    final = answer_number == len(PHASES)
    next_index = answer_number
    next_question = _question(next_index, state)
    next_phase = PHASES[min(next_index, len(PHASES) - 1)]
    state["transcript"].append({
        "speaker": "AI Interviewer",
        "content": next_question,
        "timestamp_seconds": elapsed_seconds,
        "behavioral_tags": [] if final else [next_phase[1]],
    })
    remaining = max(0, state["target_duration_minutes"] * 60 - elapsed_seconds) // 60
    response = {
        "turn_number": answer_number + 1,
        "ai_question": next_question,
        "phase_name": next_phase[0],
        "phase_target_competency": next_phase[1],
        "elapsed_seconds": elapsed_seconds,
        "target_duration_minutes": state["target_duration_minutes"],
        "turns_completed": answer_number,
        "is_final_turn": final,
        "pacing_advice": "That was the final question. Your report is being prepared." if final else f"Question {answer_number + 1} of {len(PHASES)}. About {remaining} minutes remain.",
        "acknowledgement_note": "A concrete example will make the evidence stronger." if len(clean_text.split()) < 25 else "Your answer included useful supporting detail.",
        "detected_competencies": tags,
        "delivery_feedback": _delivery_feedback(metrics),
    }
    return state, response


def _average(turns: list[dict[str, Any]], key: str) -> float | None:
    values = [turn.get("metrics", {}).get(key) for turn in turns]
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    return round(sum(numeric) / len(numeric), 1) if numeric else None


def _total(turns: list[dict[str, Any]], key: str) -> int | None:
    values = [turn.get("metrics", {}).get(key) for turn in turns]
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    return int(round(sum(numeric))) if numeric else None


def _band(score: float) -> str:
    return "Exemplary" if score >= 80 else "Proficient" if score >= 60 else "Needs Attention"


def _delivery_feedback(metrics: dict[str, Any]) -> str | None:
    pace = metrics.get("speaking_pace_wpm")
    if not isinstance(pace, (int, float)):
        return None
    if pace < 90:
        return "Your pace was measured as slow; keep the answer moving while preserving structure."
    if pace > 180:
        return "Your pace was measured as fast; pause briefly between the situation, action, and result."
    return "Your speaking pace was within a clear conversational range."


def build_report(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    turns = state.get("turns", [])
    competency_scores: dict[str, dict[str, Any]] = {}
    for competency in COMPETENCIES:
        matching = [turn for turn in turns if competency in turn.get("tags", [])]
        word_count = sum(len(turn.get("response", "").split()) for turn in matching)
        score = min(90.0, 30.0 + len(matching) * 25.0 + min(word_count, 70) * 0.5) if matching else 25.0
        evidence = matching[0]["response"][:180] if matching else "Not clearly demonstrated in the recorded answers."
        competency_scores[competency] = {
            "competency_name": competency,
            "score_percent": round(score, 1),
            "rating_band": _band(score),
            "key_evidence": evidence,
            "growth_opportunity": f"Prepare a specific situation-action-result example showing {competency.lower()}.",
        }
    overall = round(sum(item["score_percent"] for item in competency_scores.values()) / len(competency_scores), 1)
    ranked = sorted(competency_scores.values(), key=lambda item: item["score_percent"], reverse=True)
    last_elapsed = int(turns[-1].get("elapsed_seconds", 0)) if turns else 0
    minutes, seconds = divmod(last_elapsed, 60)
    face = _average(turns, "face_presence_percent")
    gaze = _average(turns, "eye_contact_percent")
    posture = _average(turns, "posture_stability_score")
    head = _average(turns, "head_movement_rate")
    wpm = _average(turns, "speaking_pace_wpm")
    pauses = _total(turns, "pauses_count")
    fillers = _total(turns, "filler_words_count")
    answered = len(turns)
    assessment = f"You completed {answered} of {len(PHASES)} interview questions with an indicative overall score of {overall:.0f}/100."
    return {
        "session_id": session_id,
        "course_id": state["course_id"],
        "course_title": state["course_title"],
        "officer_name": state["officer_name"],
        "total_duration_formatted": f"{minutes}m {seconds}s",
        "total_turns": answered,
        "overall_score_percent": overall,
        "overall_rating_band": _band(overall),
        "overall_assessment": assessment,
        "course_understanding": competency_scores["Course Knowledge"]["key_evidence"],
        "communication_assessment": f"The interview recorded {answered} answers. Use concise, structured examples to strengthen clarity.",
        "decision_making_assessment": competency_scores["Decision Making"]["key_evidence"],
        "executive_summary": assessment,
        "competency_scores": competency_scores,
        "core_strengths": [f"{item['competency_name']}: {item['key_evidence']}" for item in ranked[:2]],
        "areas_for_improvement": [f"{item['competency_name']}: {item['growth_opportunity']}" for item in ranked[-2:]],
        "priority_development_areas": [item["competency_name"] for item in ranked[-2:]],
        "recommended_upskilling": ["Revisit the course modules and connect each concept to a workplace example.", "Practise the situation-action-result answer structure."],
        "recommended_apar_actions": [],
        "conversation_analysis": "Assessment uses only the officer's recorded answers and observable browser telemetry.",
        "video_behavioural_observations": {
            "posture_stability": "Not captured" if posture is None else ("Steady" if posture >= 75 else "Some movement observed"),
            "posture_stability_score": posture,
            "head_movement_observed": "Not captured" if head is None else f"{head:.1f} measured head movements per minute",
            "gaze_alignment_percent": gaze,
            "face_presence_percent": face,
            "excessive_movement_fidgeting": "Not measured",
            "observable_summary": "Camera signals were not captured." if face is None else f"Face presence was measured at {face:.0f}%.",
        },
        "speech_analysis": {
            "average_wpm": wpm,
            "pace_assessment": "Not captured" if wpm is None else f"Average speaking pace: {wpm:.0f} words per minute",
            "pauses_frequency": "Not captured" if pauses is None else f"{pauses} measured pauses",
            "filler_word_count": fillers,
            "clarity_rating": "Not measured",
            "coherence_assessment": "Review the transcript evidence alongside the indicative competency scores.",
            "delivery_cadence": "Not captured" if wpm is None else "Measured from spoken answers in the browser.",
        },
        "transcript": state.get("transcript", []),
        "observable_signals_disclaimer": "Observable browser signals do not constitute emotional profiling, psychological diagnosis, or character judgement.",
        "evaluation_method": "Indicative rules-based scoring from the persisted interview transcript and captured telemetry.",
    }
