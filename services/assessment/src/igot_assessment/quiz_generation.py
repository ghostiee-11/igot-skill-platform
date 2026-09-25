"""Source-grounded quiz generation with validated questions and a clear fallback."""

import random
import re

import httpx


def normalize_question(raw: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None
    question = str(raw.get("question") or "").strip()
    options = raw.get("options")
    try:
        correct = int(raw.get("correct_index"))
    except (TypeError, ValueError):
        return None
    if not question or not isinstance(options, list) or len(options) != 4 or not 0 <= correct < 4:
        return None
    clean = [str(value).strip() for value in options]
    if any(not value for value in clean) or len({value.lower() for value in clean}) != 4:
        return None
    answer = clean[correct]
    random.shuffle(clean)
    return {
        "question": question,
        "options": clean,
        "correct_index": clean.index(answer),
        "explanation": str(raw.get("explanation") or f"The source supports: {answer}.").strip(),
        "concept": str(raw.get("concept") or "").strip()[:255] or None,
    }


def fallback_questions(source: str, count: int, seen: set[str]) -> list[dict]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", source) if 8 <= len(part.split()) <= 45]
    words = sorted({word for word in re.findall(r"[A-Za-z][A-Za-z-]{5,}", source)}, key=str.lower)
    results = []
    for sentence in sentences:
        candidates = re.findall(r"[A-Za-z][A-Za-z-]{5,}", sentence)
        if not candidates:
            continue
        answer = max(candidates, key=len)
        distractors = [word for word in words if word.lower() != answer.lower()]
        if len(distractors) < 3:
            continue
        question = f"Fill in the blank: {sentence.replace(answer, '_____', 1)}"
        if question.lower() in seen:
            continue
        seen.add(question.lower())
        options = random.sample(distractors, 3) + [answer]
        random.shuffle(options)
        results.append({"question": question, "options": options, "correct_index": options.index(answer), "explanation": f"The source states: {sentence}", "concept": None})
        if len(results) >= count:
            break
    return results


async def generate_questions(source: str, count: int, difficulty: str, authorization: str | None, ai_url: str) -> tuple[list[dict], str]:
    source = re.sub(r"\s+", " ", source).strip()[:24000]
    chunks = [source[index:index + 6000] for index in range(0, len(source), 6000)]
    questions = []
    seen: set[str] = set()
    if authorization:
        async with httpx.AsyncClient(timeout=40) as client:
            for chunk in chunks:
                remaining = count - len(questions)
                if remaining <= 0:
                    break
                prompt = (
                    f"Create up to {min(remaining, 10)} {difficulty} multiple-choice questions strictly grounded in the source below. "
                    "Each must have exactly four distinct options, one correct_index from 0 to 3, a source-grounded explanation, and a short concept. "
                    "Avoid trivia and 'all of the above'. Return a JSON object with a questions array.\n\nSOURCE:\n" + chunk
                )
                try:
                    response = await client.post(
                        f"{ai_url}/v1/generate/json",
                        headers={"Authorization": authorization},
                        json={"messages": [{"role": "system", "content": "You design evidence-led civil-service learning assessments. Return JSON only."}, {"role": "user", "content": prompt}], "schema_hint": {"questions": [{"question": "string", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "string", "concept": "string"}]}, "preferred_provider": "groq"},
                    )
                    response.raise_for_status()
                    batch = response.json().get("data", {}).get("questions", [])
                except (httpx.HTTPError, ValueError, TypeError, AttributeError):
                    continue
                for raw in batch if isinstance(batch, list) else []:
                    item = normalize_question(raw)
                    if item and item["question"].lower() not in seen:
                        seen.add(item["question"].lower())
                        questions.append(item)
                    if len(questions) >= count:
                        break
    generator = "llm" if questions else "fallback"
    if len(questions) < count:
        questions.extend(fallback_questions(source, count - len(questions), seen))
    return questions[:count], generator
