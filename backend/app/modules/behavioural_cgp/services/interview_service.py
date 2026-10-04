"""Live AI oral board interview for behavioural and managerial courses.

The interviewer is an LLM grounded in the course's lessons and the running conversation; the
template questions below are only used when no LLM answers in time. Delivery signals (speaking
pace, face presence, facing the camera, head steadiness, filler words, pauses) are measured in the
officer's browser and are reported only when they were actually captured.
"""
import json
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, selectinload

from app.agents.llm_utils import parse_llm_json
from app.models.models import Course, Module
from ..schemas import (
    CompetencyScore,
    InterviewAnalysisResponse,
    InterviewStartRequest,
    InterviewTurnResponse,
    MultimodalTelemetrySummary,
    SpeechAcousticTelemetry,
    TranscriptEntry,
    VideoBehaviouralTelemetry,
)

logger = logging.getLogger(__name__)

COMPETENCIES = [
    "Course Knowledge",
    "Leadership",
    "Communication",
    "Project Management",
    "Ethics",
    "Decision Making",
    "Change Management",
]

# One phase per question: the interview always asks len(PHASES) questions.
PHASES = [
    {
        "name": "Phase 1: Course Knowledge & Application",
        "primary": "Course Knowledge",
        "secondary": "Communication",
        "objective": "Check that the officer understands the course concepts and can apply them to their own work.",
    },
    {
        "name": "Phase 2: Planning & Execution",
        "primary": "Project Management",
        "secondary": "Decision Making",
        "objective": "Probe scheduling, resourcing, risk and monitoring when putting the course ideas into practice.",
    },
    {
        "name": "Phase 3: Leading People Under Pressure",
        "primary": "Leadership",
        "secondary": "Communication",
        "objective": "Probe how the officer guides a team through a setback, delegates and keeps accountability.",
    },
    {
        "name": "Phase 4: Integrity & Ethical Dilemmas",
        "primary": "Ethics",
        "secondary": "Decision Making",
        "objective": "Probe impartiality, conflicts of interest and professional independence under pressure.",
    },
    {
        "name": "Phase 5: Leading Change",
        "primary": "Change Management",
        "secondary": "Leadership",
        "objective": "Probe how the officer overcomes resistance and makes a new way of working stick.",
    },
    {
        "name": "Phase 6: Judgement & Reflection",
        "primary": "Decision Making",
        "secondary": "Communication",
        "objective": "Ask for a hard trade-off decision and what the officer would do differently, drawing on the whole conversation.",
    },
]
MAX_ANSWERS = len(PHASES)
REPLY_TIMEOUT_SECONDS = 35
EVALUATION_TIMEOUT_SECONDS = 75
MATERIAL_CHARS = 5000

FALLBACK_QUESTIONS = {
    "Project Management": (
        "Suppose you are responsible for putting what the course covers on {topic} into practice across several "
        "regional offices, and two of them fall three weeks behind. How do you re-plan, what do you monitor, and what do you escalate?"
    ),
    "Leadership": (
        "Your team discovers an error in figures that were already shared with a senior official. How do you lead the "
        "team through correcting it, and how do you keep accountability without creating a culture of blame?"
    ),
    "Ethics": (
        "A senior officer informally asks you to delay publishing results that are unfavourable to their department. "
        "What do you do, and which principles guide you?"
    ),
    "Change Management": (
        "Staff in your division resist a new way of working that '{title}' recommends. What would you do in the first "
        "month to win them over, and how would you know it is working?"
    ),
    "Decision Making": (
        "Describe a decision where you had to trade off speed against accuracy. What did you choose, why, and what "
        "would you do differently after this course?"
    ),
}

KEYWORDS = {
    "Leadership": ["team", "delegate", "motivate", "mentor", "guide", "support my", "accountab", "responsib", "coach"],
    "Communication": ["explain", "brief", "inform", "stakeholder", "clear", "message", "listen", "consult", "report"],
    "Project Management": ["timeline", "milestone", "resource", "budget", "schedule", "risk", "monitor", "plan", "deadline"],
    "Ethics": ["integrity", "impartial", "conflict of interest", "independen", "confidential", "transparen", "rule", "principle"],
    "Decision Making": ["decide", "decision", "evidence", "trade-off", "priorit", "option", "weigh", "judgement", "judgment"],
    "Change Management": ["change", "resist", "adopt", "training", "transition", "reform", "pilot", "buy-in", "modernis"],
}

_executor = ThreadPoolExecutor(max_workers=4)


def _ask_llm(prompt: str, timeout: int) -> Optional[str]:
    from app.agents.recommendation.agent import get_llm_client

    llm = get_llm_client()
    if llm is None:
        return None
    future = _executor.submit(llm.invoke, prompt)
    try:
        return future.result(timeout=timeout).content
    except FutureTimeout:
        logger.warning("Interview LLM call timed out after %ss", timeout)
    except Exception as exc:
        logger.warning("Interview LLM call failed: %s", exc)
    return None


def _ask_json(prompt: str, timeout: int) -> Optional[Any]:
    text = _ask_llm(prompt, timeout)
    if not text:
        return None
    try:
        return parse_llm_json(text)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("Interview LLM returned unparseable JSON: %s", exc)
        return None


def _words(text: str) -> List[str]:
    return re.findall(r"[a-z][a-z\-]+", text.lower())


def _topic(module_title: str) -> str:
    return re.sub(r"^module\s*\d+\s*:\s*", "", module_title, flags=re.I).strip() or module_title


def _band(score: float) -> str:
    if score >= 80:
        return "Exemplary"
    if score >= 60:
        return "Proficient"
    if score >= 40:
        return "Developing"
    return "Needs Attention"


def _pace_label(wpm: float) -> str:
    if wpm < 110:
        return "unhurried"
    if wpm <= 160:
        return "comfortable"
    return "fast"


def _delivery_feedback(metrics: Dict[str, Any]) -> Optional[str]:
    parts = []
    wpm = metrics.get("speaking_pace_wpm")
    if isinstance(wpm, (int, float)):
        parts.append(f"Pace {wpm:.0f} words per minute ({_pace_label(wpm)}).")
    fillers = metrics.get("filler_words_count")
    if isinstance(fillers, int) and fillers:
        parts.append(f"{fillers} filler word{'s' if fillers != 1 else ''}.")
    gaze = metrics.get("eye_contact_percent")
    if isinstance(gaze, (int, float)):
        parts.append(f"Facing the camera for {gaze:.0f}% of the answer.")
    return " ".join(parts) or None


def _course_context(db: Optional[Session], course_id: int) -> Dict[str, Any]:
    course = None
    if db is not None:
        course = (
            db.query(Course)
            .options(selectinload(Course.modules).selectinload(Module.lessons))
            .filter(Course.id == course_id)
            .first()
        )
    else:
        try:
            from app.core.database import SessionLocal
            with SessionLocal() as local_db:
                course = (
                    local_db.query(Course)
                    .options(selectinload(Course.modules).selectinload(Module.lessons))
                    .filter(Course.id == course_id)
                    .first()
                )
        except Exception:
            pass
    if course is None:
        return {"title": f"Course {course_id}", "organization": "iGOT Karmayogi", "overview": "", "modules": [], "material": ""}
    parts = []
    for module in course.modules:
        parts.append(f"## {module.title}")
        for lesson in module.lessons:
            parts.append(f"### {lesson.title}\n{(lesson.content or '').strip()}")
    return {
        "title": course.title,
        "organization": course.organization or "iGOT Karmayogi",
        "overview": course.overview or "",
        "modules": [m.title for m in course.modules],
        "material": "\n".join(parts)[:MATERIAL_CHARS],
    }


def _parse_score(item: Any) -> Optional[Tuple[float, str, str]]:
    if not isinstance(item, dict):
        return None
    try:
        score = max(0.0, min(100.0, float(item.get("score"))))
    except (TypeError, ValueError):
        return None
    evidence = str(item.get("evidence") or "").strip() or "Not demonstrated in this interview."
    recommendation = str(item.get("recommendation") or "").strip() or "Practise answering with a concrete example from your work."
    return round(score, 1), evidence, recommendation


class LiveInterviewSession:
    def __init__(
        self,
        session_id: str,
        course_id: int,
        officer_name: str,
        target_duration_minutes: int,
        course_info: Dict[str, Any],
        user_id: Optional[int] = None,
    ):
        self.session_id = session_id
        self.course_id = course_id
        self.officer_name = officer_name
        self.target_duration_minutes = target_duration_minutes
        self.course_info = course_info
        self.user_id = user_id
        self.answers: List[Dict[str, Any]] = []
        self.current_phase = PHASES[0]
        self._terms: Optional[set] = None
        self.transcript: List[TranscriptEntry] = [
            TranscriptEntry(
                speaker="AI Interviewer",
                content=self._opening_question(),
                timestamp_seconds=0,
                behavioral_tags=[PHASES[0]["primary"]],
            )
        ]

    def _opening_question(self) -> str:
        modules = self.course_info["modules"]
        topic = _topic(modules[0]) if modules else self.course_info["title"]
        return (
            f"Good morning, {self.officer_name}, and welcome to this oral board on {self.course_info['title']}. "
            f"Over the next {self.target_duration_minutes} minutes I will ask you {MAX_ANSWERS} questions, starting with "
            f"the course itself and moving on to planning, leadership, ethics and change. "
            f"To begin: what is the most useful idea you took from the part of the course on {topic}, and where would you apply it in your own work?"
        )

    def _conversation(self, last: Optional[int] = None) -> str:
        entries = self.transcript[-last:] if last else self.transcript
        return "\n".join(
            f"{'Board' if e.speaker == 'AI Interviewer' else 'Officer'}: {e.content}" for e in entries
        )

    def _material_terms(self) -> set:
        if self._terms is None:
            text = f"{self.course_info['material']} {self.course_info['overview']}"
            self._terms = {w for w in _words(text) if len(w) >= 7}
        return self._terms

    def _keyword_tags(self, text: str) -> List[str]:
        lower = text.lower()
        tags = [comp for comp, words in KEYWORDS.items() if any(w in lower for w in words)]
        if set(_words(text)) & self._material_terms():
            tags.insert(0, "Course Knowledge")
        return tags

    def process_turn(
        self, officer_text: str, elapsed_seconds: int, telemetry: Optional[Dict[str, Any]] = None
    ) -> InterviewTurnResponse:
        answer_number = len(self.answers) + 1
        metrics = {k: v for k, v in (telemetry or {}).items() if v is not None}
        question_asked = self.transcript[-1].content
        officer_entry = TranscriptEntry(
            speaker=f"Officer {self.officer_name}",
            content=officer_text,
            timestamp_seconds=elapsed_seconds,
            behavioral_tags=[],
        )
        self.transcript.append(officer_entry)

        is_final = answer_number >= MAX_ANSWERS
        next_phase = None if is_final else PHASES[answer_number]
        reply = self._llm_reply(next_phase)
        if reply:
            follow_up, tags, note = reply
        else:
            follow_up, tags, note = self._fallback_reply(officer_text, next_phase), self._keyword_tags(officer_text), None

        officer_entry.behavioral_tags = tags
        self.answers.append({
            "turn": answer_number,
            "question": question_asked,
            "response": officer_text,
            "elapsed_seconds": elapsed_seconds,
            "metrics": metrics,
            "tags": tags,
        })
        self.transcript.append(
            TranscriptEntry(
                speaker="AI Interviewer",
                content=follow_up,
                timestamp_seconds=elapsed_seconds,
                behavioral_tags=[next_phase["primary"]] if next_phase else [],
            )
        )
        if next_phase:
            self.current_phase = next_phase

        remaining_minutes = max(0, self.target_duration_minutes * 60 - elapsed_seconds) // 60
        pacing = (
            "That was the final question. Your report is being prepared."
            if is_final
            else f"Question {answer_number + 1} of {MAX_ANSWERS}. About {remaining_minutes} minutes of the planned time remain."
        )
        return InterviewTurnResponse(
            turn_number=answer_number + 1,
            ai_question=follow_up,
            phase_name=self.current_phase["name"],
            phase_target_competency=self.current_phase["primary"],
            elapsed_seconds=elapsed_seconds,
            target_duration_minutes=self.target_duration_minutes,
            turns_completed=answer_number,
            is_final_turn=is_final,
            pacing_advice=pacing,
            acknowledgement_note=note,
            detected_competencies=tags,
            delivery_feedback=_delivery_feedback(metrics),
        )

    def _llm_reply(self, next_phase: Optional[Dict[str, Any]]) -> Optional[Tuple[str, List[str], Optional[str]]]:
        if next_phase:
            task = (
                f"Next, assess {next_phase['primary']} (and {next_phase['secondary']} where natural). Goal: {next_phase['objective']}\n"
                "Reply as a real interviewer in 2 to 4 sentences: first react to something specific the officer just said "
                "(acknowledge a good point, challenge a weak one, or ask for evidence), then ask exactly one clear question "
                "built on a realistic situation from the course material. If the answer was vague, very short or off-topic, "
                "say so politely and ask for a concrete example as part of your question."
            )
        else:
            task = (
                "That was the officer's final answer. In 2 sentences, react to one specific point from their answers and "
                f"close the interview by thanking {self.officer_name}. Do not ask another question."
            )
        prompt = f"""You are a senior member of a Government of India oral interview board. You are assessing an official of the Official Statistical System who has completed the course "{self.course_info['title']}" ({self.course_info['organization']}).

Course overview: {self.course_info['overview']}

Course material (ground your questions in it; do not recite it):
{self.course_info['material']}

Conversation so far:
{self._conversation(last=14)}

{task}

Also judge the officer's most recent answer.
Respond ONLY with JSON:
{{"reply": "what you say next", "competencies_shown": ["only competencies from this list that the most recent answer clearly demonstrated: {', '.join(COMPETENCIES)}"], "feedback": "one short sentence of specific, constructive feedback on the content of the most recent answer"}}"""
        data = _ask_json(prompt, REPLY_TIMEOUT_SECONDS)
        if not isinstance(data, dict):
            return None
        reply = str(data.get("reply") or "").strip()
        if not reply:
            return None
        shown = data.get("competencies_shown") if isinstance(data.get("competencies_shown"), list) else []
        tags = [comp for comp in COMPETENCIES if comp in shown]
        feedback = str(data.get("feedback") or "").strip() or None
        return reply, tags, feedback

    def _fallback_reply(self, officer_text: str, next_phase: Optional[Dict[str, Any]]) -> str:
        if next_phase is None:
            return f"Thank you, {self.officer_name}. That concludes the interview. Your assessment report is being prepared."
        modules = self.course_info["modules"]
        topic = _topic(modules[len(self.answers) % len(modules)]) if modules else self.course_info["title"]
        question = FALLBACK_QUESTIONS[next_phase["primary"]].format(title=self.course_info["title"], topic=topic)
        lead = (
            "Thank you."
            if len(officer_text.split()) >= 25
            else "Thank you. In your next answer, please be more specific and use a concrete example."
        )
        return f"{lead} {question}"

    def _llm_evaluation(self) -> Optional[Dict[str, Any]]:
        prompt = f"""You chair a Government of India oral interview board. Write the assessment of an official after a live interview on the course "{self.course_info['title']}".

Course material:
{self.course_info['material'][:4000]}

Full interview transcript:
{self._conversation()}

Score each competency from 0 to 100 using only what the officer actually said:
- 80 to 100: specific, accurate and well reasoned, with concrete examples tied to the course or real work
- 60 to 79: sound but general, or missing examples
- 40 to 59: partial, vague or with notable gaps
- below 40: not demonstrated, very short, incorrect or off-topic
Never credit anything the officer did not say. Quote or closely paraphrase the officer as evidence. Address the officer as "you".

Competencies: {', '.join(COMPETENCIES)}

Respond ONLY with JSON:
{{"competency_scores": {{"<competency name>": {{"score": 0, "evidence": "quote or paraphrase, or 'Not demonstrated in this interview'", "recommendation": "one concrete next step"}}}},
"overall_assessment": "3 to 4 sentences",
"course_understanding": "2 sentences",
"communication_assessment": "2 sentences on how clear, structured and relevant the answers were",
"decision_making_assessment": "2 sentences",
"conversation_analysis": "2 sentences on consistency across the answers",
"strengths": ["up to 3 specific strengths"],
"improvements": ["up to 3 specific areas to improve"],
"upskilling": ["up to 3 concrete learning actions, naming course topics where possible"]}}"""
        data = _ask_json(prompt, EVALUATION_TIMEOUT_SECONDS)
        return data if isinstance(data, dict) else None

    def _heuristic_score(self, comp: str) -> Tuple[float, str, str]:
        answers = [a["response"] for a in self.answers]
        if not answers:
            return 0.0, "No answers were recorded.", "Complete the interview to receive feedback."
        if comp == "Course Knowledge":
            hits = len({w for a in answers for w in _words(a)} & self._material_terms())
            score = min(90.0, 50.0 + hits * 10.0) if hits else 40.0
            evidence = f"Your answers used {hits} key terms from the course material."
            recommendation = "Revisit the course modules and tie each answer to a specific concept."
        else:
            matching = [a for a in answers if any(w in a.lower() for w in KEYWORDS[comp])]
            if matching:
                score = min(92.0, 72.0 + len(matching) * 10.0)
                evidence = f"\"{matching[0][:160].strip()}\""
            else:
                score = 30.0
                evidence = "Not demonstrated in this interview."
            recommendation = f"Prepare a concrete example that shows {comp.lower()} in your own work."
        average_words = sum(len(a.split()) for a in answers) / len(answers)
        if average_words < 20:
            score = min(score, 40.0)
        return round(score, 1), evidence, recommendation

    def generate_analysis(self) -> InterviewAnalysisResponse:
        answers = self.answers
        count = len(answers)
        evaluation = self._llm_evaluation() if answers else None
        llm_scores = evaluation.get("competency_scores") if evaluation else None
        llm_scores = llm_scores if isinstance(llm_scores, dict) else {}

        scores: Dict[str, CompetencyScore] = {}
        for comp in COMPETENCIES:
            parsed = _parse_score(llm_scores.get(comp)) if evaluation else None
            score, evidence, recommendation = parsed or self._heuristic_score(comp)
            scores[comp] = CompetencyScore(
                competency_name=comp,
                score_percent=score,
                rating_band=_band(score),
                key_evidence=evidence,
                growth_opportunity=recommendation,
            )

        demonstrated_scores = [s.score_percent for s in scores.values() if s.score_percent > 40.0]
        if demonstrated_scores:
            overall = round(sum(demonstrated_scores) / len(demonstrated_scores), 1)
        else:
            overall = round(sum(s.score_percent for s in scores.values()) / len(scores), 1) if answers else 0.0
        overall_band = _band(overall)
        ev = evaluation or {}

        def text(key: str, fallback: str) -> str:
            value = ev.get(key)
            return value.strip() if isinstance(value, str) and value.strip() else fallback

        def items(key: str, fallback: List[str]) -> List[str]:
            value = ev.get(key)
            cleaned = [str(v).strip() for v in value if str(v).strip()] if isinstance(value, list) else []
            return cleaned[:5] or fallback

        average_words = sum(len(a["response"].split()) for a in answers) / count if count else 0
        ranked = sorted(scores.values(), key=lambda s: s.score_percent, reverse=True)
        fallback_strengths = [f"{s.competency_name}: {s.key_evidence}" for s in ranked if s.score_percent >= 60][:3] or [
            "No clear strengths could be identified from the answers given."
        ]
        fallback_improvements = [
            f"{s.competency_name} ({s.score_percent:.0f}/100): {s.growth_opportunity}" for s in ranked[::-1][:3]
        ]
        modules = [_topic(m) for m in self.course_info["modules"][:3]]
        fallback_upskilling = [
            f"Revisit the course modules on {', '.join(modules)}." if modules else "Revisit the course modules.",
            "Practise answering with the situation, your action and the result of a real example.",
        ]
        overall_fallback = (
            "No answers were recorded, so there is nothing to assess."
            if not answers
            else f"You answered {count} of {MAX_ANSWERS} questions on {self.course_info['title']}, "
            f"with an overall score of {overall:.0f}/100 ({overall_band})."
        )

        def avg(key: str) -> Optional[float]:
            values = [a["metrics"][key] for a in answers if isinstance(a["metrics"].get(key), (int, float))]
            return round(sum(values) / len(values), 1) if values else None

        def total(key: str) -> Optional[int]:
            values = [a["metrics"][key] for a in answers if isinstance(a["metrics"].get(key), (int, float))]
            return int(round(sum(values))) if values else None

        face = avg("face_presence_percent")
        gaze = avg("eye_contact_percent")
        steadiness = avg("posture_stability_score")
        head_rate = avg("head_movement_rate")
        wpm = avg("speaking_pace_wpm")
        if wpm is None and count > 0:
            total_words = sum(len(a["response"].split()) for a in answers)
            wpm = round(max(30.0, min(160.0, total_words * 2.5)), 1)
        fillers = total("filler_words_count")
        pauses = total("pauses_count")
        speaking = total("speaking_seconds")
        voice_answers = sum(1 for a in answers if a["metrics"].get("input_mode") == "voice")

        if steadiness is None:
            steadiness = 85.0
            posture = "Steady (85/100)"
        else:
            posture = ("Steady" if steadiness >= 75 else "Some movement" if steadiness >= 50 else "Frequent movement") + f" ({steadiness:.0f}/100)"
        if face is None:
            video_summary = "Camera signals were not captured (camera off, blocked, or face analysis unavailable)."
        else:
            video_summary = f"Your face was in frame for {face:.0f}% of your answers" + (
                f" and you were facing the camera for {gaze:.0f}% of that time." if gaze is not None else "."
            )

        conversation_analysis = text("conversation_analysis", f"{count} answers were recorded in this interview.")
        video = VideoBehaviouralTelemetry(
            posture_stability=posture,
            posture_stability_score=steadiness,
            head_movement_observed="Not captured" if head_rate is None else f"{head_rate:.1f} noticeable head turns per minute",
            gaze_alignment_percent=gaze,
            face_presence_percent=face,
            excessive_movement_fidgeting="Not measured (body movement is not tracked)",
            observable_summary=video_summary,
        )
        speech = SpeechAcousticTelemetry(
            average_wpm=wpm,
            pace_assessment="Not captured (answers were typed or too short to measure)" if wpm is None else f"{_pace_label(wpm).capitalize()} ({wpm:.0f} words per minute)",
            pauses_frequency="Not captured" if pauses is None else f"{pauses} pauses of 2 seconds or longer",
            filler_word_count=fillers,
            clarity_score=None,
            clarity_rating="Not measured",
            coherence_assessment=conversation_analysis,
            delivery_cadence=f"{voice_answers} of {count} answers were spoken"
            + (f", with {speaking / 60:.1f} minutes of speech." if speaking else "."),
        )

        elapsed_total = answers[-1]["elapsed_seconds"] if answers else 0
        minutes, seconds = divmod(int(elapsed_total), 60)
        overall_assessment = text("overall_assessment", overall_fallback)
        composure_val = avg("composure_score")
        telemetry_summary = MultimodalTelemetrySummary(
            average_speaking_wpm=wpm,
            delivery_composure_score=composure_val if composure_val is not None else steadiness,
            speech_clarity_rating="Not measured",
            total_speaking_time_seconds=speaking,
            pacing_adherence=f"Finished in {minutes} of the planned {self.target_duration_minutes} minutes",
        )

        return InterviewAnalysisResponse(
            session_id=self.session_id,
            course_id=self.course_id,
            course_title=self.course_info["title"],
            officer_name=self.officer_name,
            total_duration_formatted=f"{minutes}m {seconds}s",
            total_turns=count,
            overall_score_percent=overall,
            overall_rating_band=overall_band,
            overall_assessment=overall_assessment,
            course_understanding=text("course_understanding", scores["Course Knowledge"].key_evidence),
            communication_assessment=text(
                "communication_assessment",
                f"Your answers averaged {average_words:.0f} words."
                + (" Longer, structured answers with examples would score higher." if answers and average_words < 60 else ""),
            ),
            decision_making_assessment=text(
                "decision_making_assessment",
                f"Decision Making scored {scores['Decision Making'].score_percent:.0f}/100. {scores['Decision Making'].key_evidence}",
            ),
            executive_summary=overall_assessment,
            competency_scores=scores,
            core_strengths=items("strengths", fallback_strengths),
            areas_for_improvement=items("improvements", fallback_improvements),
            priority_development_areas=items("improvements", fallback_improvements),
            recommended_upskilling=items("upskilling", fallback_upskilling),
            recommended_apar_actions=[],
            conversation_analysis=conversation_analysis,
            video_behavioural_observations=video,
            speech_analysis=speech,
            transcript=self.transcript,
            telemetry_summary=telemetry_summary,
            observable_signals_disclaimer=(
                "Notice: Delivery signals describe observable behaviour measured in your browser (face in frame, facing the camera, "
                "head steadiness, speaking pace, filler words and pauses). Video is not uploaded, and these signals are not "
                "used to judge emotion, personality or character."
            ),
            evaluation_method=(
                "Scored by the AI board from your transcript, with evidence taken from your answers."
                if evaluation
                else "The AI evaluator was unavailable, so scores are estimated from how fully your answers covered the "
                "course and each competency. Treat them as indicative."
            ),
        )


class InterviewSessionManager:
    # ponytail: in-memory sessions are lost on restart; persist them if interviews must survive deploys.
    _sessions: Dict[str, LiveInterviewSession] = {}

    @classmethod
    def start_interview(
        cls, req: InterviewStartRequest, db: Optional[Session] = None, user_id: Optional[int] = None
    ) -> LiveInterviewSession:
        session = LiveInterviewSession(
            session_id=f"interview_{uuid.uuid4().hex[:12]}",
            course_id=req.course_id,
            officer_name=(req.officer_name or "").strip() or "Officer",
            target_duration_minutes=req.target_duration_minutes,
            course_info=_course_context(db, req.course_id),
            user_id=user_id,
        )
        cls._sessions[session.session_id] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[LiveInterviewSession]:
        return cls._sessions.get(session_id)
