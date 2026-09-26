"""Server-owned assessment engine implementations."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol

class AssessmentEngine(Protocol):
    name: str
    def start(self, definition: dict[str, Any]) -> dict[str, Any]: ...
    def submit(self, state: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]: ...
    def finalize(self, state: dict[str, Any]) -> dict[str, Any]: ...

def _level(score: float) -> str:
    if score >= 90: return "master"
    if score >= 75: return "advanced"
    if score >= 50: return "intermediate"
    if score >= 25: return "basic"
    return "novice"

def public_state(state: dict[str, Any]) -> dict[str, Any]:
    """Remove answer keys and scoring rules from learner responses."""
    items, cursor = state.get("items", []), state.get("cursor", 0)
    current = items[cursor] if cursor < len(items) else None
    if current:
        current = {"id": current["id"], "text": current["text"], "options": [
            ({k: v for k, v in option.items() if k in {"id", "text", "label"}}
             if isinstance(option, dict) else {"id": index, "text": str(option)})
            for index, option in enumerate(current.get("options", []))]}
    return {"cursor": cursor, "total_items": len(items), "completed": cursor >= len(items),
            "current_item": current, "responses_count": len(state.get("responses", [])),
            **({"mastery": state["mastery"]} if "mastery" in state else {}),
            **({"next_action": state["next_action"]} if state.get("next_action") else {})}

@dataclass
class ChoiceEngine:
    name: str
    domain_code: str
    def start(self, definition: dict[str, Any]) -> dict[str, Any]:
        items = definition.get("items") or []
        if not items: raise ValueError("assessment has no server-owned items")
        competency_codes = list(definition.get("competency_codes", []))
        if definition.get("competency_code") and definition["competency_code"] not in competency_codes:
            competency_codes.append(definition["competency_code"])
        return {"items": items, "cursor": 0, "responses": [],
                "competency_codes": competency_codes,
                "pass_threshold_percent": float(definition.get("pass_threshold_percent", 60))}
    def submit(self, state: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
        cursor = int(state["cursor"])
        if cursor >= len(state["items"]): raise ValueError("session already complete")
        item = state["items"][cursor]; selected = answer.get("option_id", answer.get("selected_option")); options = item.get("options", [])
        matched = next(
            ((index, option) for index, option in enumerate(options)
             if str(option.get("id", index) if isinstance(option, dict) else index) == str(selected)),
            None,
        )
        if matched is None: raise ValueError("selected option does not exist")
        selected_index, option = matched
        correct_index = item.get("correct_option_index"); selected_index = options.index(option)
        correct = selected_index == correct_index if correct_index is not None else bool(isinstance(option, dict) and option.get("is_optimal"))
        delta = float(option.get("compliance_delta", option.get("score", 100 if correct else 0))) if isinstance(option, dict) else (100 if correct else 0)
        state["responses"].append({"item_id": item["id"], "selected_option": selected, "correct": correct,
            "score": max(0.0, min(100.0, delta)), "competency_code": item.get("competency_code")})
        state["cursor"] = cursor + 1; return state
    def finalize(self, state: dict[str, Any]) -> dict[str, Any]:
        if state["cursor"] < len(state["items"]): raise ValueError("all assessment items must be answered before finalization")
        responses = state["responses"]; score = round(sum(r["score"] for r in responses) / max(len(responses), 1), 2)
        codes = set(state.get("competency_codes", [])) | {r["competency_code"] for r in responses if r.get("competency_code")}
        evidence=[]
        for code in sorted(codes):
            relevant=[r for r in responses if not r.get("competency_code") or r.get("competency_code")==code]
            item_score=sum(r["score"] for r in relevant)/max(len(relevant),1)
            evidence.append({"competency_code":code,"domain_code":self.domain_code,"level":round(item_score/20,2)})
        return {"score_percent":score,"passed":score>=state["pass_threshold_percent"],"responses":responses,"evidence":evidence}

class StatisticalEngine(ChoiceEngine):
    """Interpretable mastery algorithm ported from the legacy statistical engine."""
    increment, decrement = 12.0, 8.0
    def start(self, definition: dict[str, Any]) -> dict[str, Any]:
        state=super().start(definition); state["mastery"]=max(0.0,min(100.0,float(definition.get("prior_mastery",0))))
        state["confidence"]=max(.1,min(1.0,float(definition.get("confidence",.5)))); state["consecutive_errors"]=0; return state
    def submit(self,state:dict[str,Any],answer:dict[str,Any])->dict[str,Any]:
        super().submit(state,answer); response=state["responses"][-1]
        if response["correct"]:
            state["mastery"]=min(100.0,state["mastery"]+self.increment);state["confidence"]=min(1.0,state["confidence"]+.08);state["consecutive_errors"]=0
        else:
            state["mastery"]=max(0.0,state["mastery"]-self.decrement);state["confidence"]=max(.1,state["confidence"]-.06);state["consecutive_errors"]+=1
        item=state["items"][state["cursor"]-1];skill=item.get("competency_code","statistical")
        prerequisites={"price.cpi.weighted_price_relatives":"price.price_relative","price.fisher_index":"price.laspeyres_index"}
        kind="remediation" if state["consecutive_errors"]>=2 else ("advance" if response["correct"] and state["mastery"]>=80 else "question")
        state["next_action"]={"type":kind,"target_skill_id":prerequisites.get(skill,skill) if kind=="remediation" else skill}
        state["mastery"],state["confidence"]=round(state["mastery"],1),round(state["confidence"],2);return state
    def finalize(self,state:dict[str,Any])->dict[str,Any]:
        result=super().finalize(state);result.update({"mastery":state["mastery"],"mastery_level":_level(state["mastery"]),"confidence":state["confidence"]})
        for evidence in result["evidence"]:evidence["level"]=round(state["mastery"]/20,2)
        return result

REGISTRY:dict[str,AssessmentEngine]={"course_quiz":ChoiceEngine("course_quiz","course"),"statistical":StatisticalEngine("statistical","statistical"),"behavioural":ChoiceEngine("behavioural","behavioural"),"technical":ChoiceEngine("technical","technical"),"digital_governance":ChoiceEngine("digital_governance","digital_governance")}
