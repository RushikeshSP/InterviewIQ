"""InterviewIQ evaluator agent, session memory, aggregation, and coach."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

from tools import check_star_structure, detect_filler_words, score_relevance

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
OFFLINE = os.getenv("INTERVIEWIQ_OFFLINE", "false").lower() in {"1", "true", "yes"}

SYSTEM_PROMPT = """You are InterviewIQ, an encouraging mock-interview evaluator.
Your job is to evaluate the candidate's current answer using the provided local tools.

Tool-selection rules:
- Always call score_relevance because every answer needs a 0-100 relevance score.
- Call detect_filler_words for every answer. It is deterministic and should be used to flag spoken-style fillers.
- Call check_star_structure for behavioral questions. Skip it for clearly technical questions.
- Do not invent tool results.
- After tools return, write short, specific, encouraging feedback. Mention one strength and at most two improvements.
- Never change or recalculate a score returned by a tool.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "detect_filler_words",
            "description": "Detect common filler words in the candidate answer.",
            "parameters": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_star_structure",
            "description": "Check Situation, Task, Action, Result components in a behavioral answer.",
            "parameters": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_relevance",
            "description": "Score answer relevance 0-100 using expected concepts for the current interview question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "expected_keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["question", "answer", "expected_keywords"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "detect_filler_words": detect_filler_words,
    "check_star_structure": check_star_structure,
    "score_relevance": score_relevance,
}


def _build_client() -> Any | None:
    key = os.getenv("GROQ_API_KEY")
    if OFFLINE or not key or key == "your_groq_api_key_here":
        return None
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The openai package is required for LLM mode. Run: pip install -r requirements.txt") from exc
    return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")


@dataclass
class EvaluationRecord:
    question_id: str
    question: str
    category: str
    answer: str
    tools_used: list[str]
    results: dict[str, dict[str, Any]]
    feedback: str

    @property
    def relevance_score(self) -> int:
        return int(self.results["score_relevance"]["score"])


@dataclass
class InterviewSession:
    records: list[EvaluationRecord] = field(default_factory=list)

    def add(self, record: EvaluationRecord) -> None:
        self.records.append(record)

    def average_relevance(self) -> float:
        if not self.records:
            return 0.0
        return round(sum(r.relevance_score for r in self.records) / len(self.records), 1)

    def weakest_record(self) -> EvaluationRecord | None:
        if not self.records:
            return None
        return min(self.records, key=lambda r: r.relevance_score)

    def to_scorecard(self) -> list[list[Any]]:
        rows: list[list[Any]] = []
        for idx, record in enumerate(self.records, 1):
            fillers = record.results.get("detect_filler_words", {}).get("total_count", 0)
            star = record.results.get("check_star_structure")
            star_text = "—"
            if star:
                star_text = f"{len(star['present'])}/4"
            rows.append([
                idx,
                record.category.title(),
                record.question,
                record.relevance_score,
                fillers,
                star_text,
                record.feedback,
            ])
        return rows

    def context_for_coach(self) -> str:
        if not self.records:
            return "No answers have been evaluated yet."
        lines = [
            f"Questions answered: {len(self.records)}",
            f"Average relevance: {self.average_relevance()}",
        ]
        weakest = self.weakest_record()
        if weakest:
            lines.append(f"Weakest area/question: {weakest.question} (score {weakest.relevance_score})")
        lines.append("Detailed session history:")
        for idx, r in enumerate(self.records, 1):
            lines.append(
                f"{idx}. [{r.category}] {r.question} | score={r.relevance_score} | "
                f"fillers={r.results.get('detect_filler_words', {}).get('total_count', 0)}"
            )
        return "\n".join(lines)


def _local_select_tools(category: str) -> list[str]:
    selected = ["score_relevance", "detect_filler_words"]
    if category.lower() == "behavioral":
        selected.append("check_star_structure")
    return selected


def _execute_local_tools(tool_names: list[str], question: dict, answer: str) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name in tool_names:
        if name == "detect_filler_words":
            results[name] = detect_filler_words(answer)
        elif name == "check_star_structure":
            results[name] = check_star_structure(answer)
        elif name == "score_relevance":
            results[name] = score_relevance(question["question"], answer, question["expected_keywords"])
    return results


def _llm_tool_loop(client: OpenAI, question: dict, answer: str) -> tuple[list[str], dict[str, dict[str, Any]], str]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Interview question ({question['category']}): {question['question']}\n"
                f"Expected concepts: {json.dumps(question['expected_keywords'])}\n"
                f"Candidate answer:\n{answer}"
            ),
        },
    ]
    used: list[str] = []
    results: dict[str, dict[str, Any]] = {}

    for _ in range(3):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=700,
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        if not tool_calls:
            return used, results, message.content or "Your answer has been evaluated."

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.function.name, "arguments": call.function.arguments},
                }
                for call in tool_calls
            ],
        })

        for call in tool_calls:
            name = call.function.name
            if name not in TOOL_FUNCTIONS:
                continue
            args = json.loads(call.function.arguments or "{}")
            if name == "detect_filler_words":
                result = detect_filler_words(args["answer"])
            elif name == "check_star_structure":
                result = check_star_structure(args["answer"])
            else:
                result = score_relevance(args["question"], args["answer"], args["expected_keywords"])
            results[name] = result
            if name not in used:
                used.append(name)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": name,
                "content": json.dumps(result),
            })

    # Safety fallback if a model keeps requesting tools.
    final = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="none",
        temperature=0.2,
        max_tokens=300,
    )
    return used, results, final.choices[0].message.content or "Good effort. Keep your answer focused on the question and include concrete examples."


def evaluate_answer(session: InterviewSession, question: dict, answer: str) -> EvaluationRecord:
    """Evaluate a single answer, persist it to session memory, and return the record."""
    answer = (answer or "").strip()
    if not answer:
        raise ValueError("Answer cannot be empty.")

    client = _build_client()
    if client is None:
        used = _local_select_tools(question["category"])
        results = _execute_local_tools(used, question, answer)
        feedback = _offline_feedback(question, results)
    else:
        used, results, feedback = _llm_tool_loop(client, question, answer)

        # Ensure mandatory deterministic metrics exist even if the model under-calls tools.
        mandatory = _local_select_tools(question["category"])
        for tool_name in mandatory:
            if tool_name not in results:
                results.update(_execute_local_tools([tool_name], question, answer))
                if tool_name not in used:
                    used.append(tool_name)

    record = EvaluationRecord(
        question_id=question["id"],
        question=question["question"],
        category=question["category"],
        answer=answer,
        tools_used=used,
        results=results,
        feedback=feedback.strip(),
    )
    session.add(record)
    return record


def _offline_feedback(question: dict, results: dict[str, dict[str, Any]]) -> str:
    score = results["score_relevance"]["score"]
    matched = results["score_relevance"]["matched_concepts"]
    filler_count = results["detect_filler_words"]["total_count"]
    if score >= 75:
        strength = "Strong relevance — your answer covers the main concepts the question is looking for."
    elif score >= 50:
        strength = "Your answer is on the right track, but you can connect it more directly to the question."
    else:
        strength = "You made an attempt; the biggest opportunity is to add the core concepts the question is testing."

    improvements = []
    if question["category"] == "behavioral":
        star = results.get("check_star_structure")
        if star and star["missing"]:
            improvements.append("add the missing STAR pieces: " + ", ".join(star["missing"]) + ".")
    if filler_count:
        improvements.append(f"reduce filler words ({filler_count} detected).")
    if not improvements:
        improvements.append("add one concrete example or measurable outcome to make the answer stronger.")
    matched_text = ", ".join(matched[:3]) if matched else "none yet"
    return f"{strength} Matched concepts: {matched_text}. Focus next on {improvements[0]}"


def generate_final_report(session: InterviewSession) -> str:
    """Generate a session-level report with actual aggregation."""
    if not session.records:
        return "## InterviewIQ Final Report\n\nNo answers have been evaluated yet."

    average = session.average_relevance()
    weakest = session.weakest_record()
    scores = [r.relevance_score for r in session.records]
    best = max(scores)
    filler_total = sum(r.results.get("detect_filler_words", {}).get("total_count", 0) for r in session.records)

    observations = []
    if average >= 75:
        observations.append("Your answers were consistently relevant to the questions.")
    elif average >= 50:
        observations.append("Your answers showed partial alignment with the questions; tighter targeting would improve consistency.")
    else:
        observations.append("Several answers missed key concepts, so focusing on the exact question being asked should be a priority.")

    observations.append(f"Your highest relevance score was {best}/100, while the lowest was {weakest.relevance_score}/100.")
    observations.append(f"Across the session, {filler_total} common filler-word instances were detected.")

    if any("check_star_structure" in r.results for r in session.records):
        star_coverages = [r.results["check_star_structure"]["coverage"] for r in session.records if "check_star_structure" in r.results]
        observations.append(f"Behavioral-answer STAR coverage averaged {round(sum(star_coverages) / len(star_coverages))}/100.")

    return (
        "## InterviewIQ Final Report\n\n"
        f"**Questions answered:** {len(session.records)}\n\n"
        f"**Average relevance score:** {average}/100\n\n"
        f"**Weakest area:** {weakest.question} ({weakest.relevance_score}/100)\n\n"
        "### Overall performance observations\n\n"
        + " ".join(observations)
        + "\n\n### Question-by-question scores\n\n"
        + "\n".join(f"{i}. **{r.relevance_score}/100** — {r.question}" for i, r in enumerate(session.records, 1))
    )


def ask_agent(session: InterviewSession, user_question: str) -> str:
    """Answer a meta-question using the entire session history and computed metrics."""
    user_question = (user_question or "").strip()
    if not user_question:
        raise ValueError("Coach question cannot be empty.")
    context = session.context_for_coach()

    client = _build_client()
    if client is None:
        return _offline_coach_answer(session, user_question)

    prompt = (
        "You are the InterviewIQ coach. Answer the candidate's meta-question using ONLY the structured "
        "session data below. Do not invent scores. Be concise, encouraging, and actionable.\n\n"
        f"SESSION DATA:\n{context}\n\nCOACH QUESTION:\n{user_question}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a precise interview coach. Use the provided session metrics as ground truth."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=350,
    )
    return response.choices[0].message.content or _offline_coach_answer(session, user_question)


def _offline_coach_answer(session: InterviewSession, user_question: str) -> str:
    if not session.records:
        return "You have not answered any questions yet. Start with the current question and I’ll track your progress."
    average = session.average_relevance()
    weakest = session.weakest_record()
    return (
        f"So far you have answered {len(session.records)} question(s) with an average relevance score of {average}/100. "
        f"Your weakest area is **{weakest.question}** at {weakest.relevance_score}/100. "
        "Focus on answering the exact question, using concrete evidence, and keeping your structure clear."
    )
