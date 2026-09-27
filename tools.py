"""Deterministic, rule-based evaluation tools for InterviewIQ."""

from __future__ import annotations

import re
from typing import Iterable


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _word_pattern(word: str) -> str:
    """Allow a small set of normal English inflections without doing semantic matching."""
    word = re.escape(word)
    if word.endswith("y"):
        return word[:-1] + r"(?:y|ies)"
    return word + r"(?:s|es|ed|ing)?"


def _term_pattern(term: str) -> re.Pattern[str]:
    """Build a case-insensitive pattern that handles common grammatical variants."""
    words = _normalize(term).split()
    pattern = r"\s+".join(_word_pattern(word) for word in words)
    return re.compile(rf"(?<!\w){pattern}(?!\w)", re.IGNORECASE)


FILLER_WORDS = ("um", "like", "basically")


def detect_filler_words(answer: str) -> dict:
    """Detect common filler words and return structured counts/evidence."""
    answer = answer or ""
    counts: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}
    for filler in FILLER_WORDS:
        matches = list(_term_pattern(filler).finditer(answer))
        counts[filler] = len(matches)
        evidence[filler] = [answer[max(0, m.start() - 20): min(len(answer), m.end() + 20)].strip() for m in matches[:3]]

    total = sum(counts.values())
    present = [word for word in FILLER_WORDS if counts[word] > 0]
    return {
        "tool": "detect_filler_words",
        "filler_words": present,
        "counts": counts,
        "total_count": total,
        "has_fillers": total > 0,
        "feedback_level": "high" if total >= 5 else "medium" if total >= 2 else "low",
        "evidence": evidence,
    }


_STAR_CUES = {
    "Situation": (
        "when ", "at my previous", "in my last", "during", "while working", "our team",
        "the project", "the customer", "we were", "i was working on", "the context",
    ),
    "Task": (
        "my responsibility", "i had to", "i was asked", "my goal", "the goal was", "needed to",
        "responsible for", "my task", "objective",
    ),
    "Action": (
        "i decided", "i implemented", "i created", "i changed", "i analyzed", "i debugged",
        "i worked", "i coordinated", "i communicated", "i tested", "i designed", "i used",
        "i wrote", "i built", "i proposed", "i took",
    ),
    "Result": (
        "as a result", "resulted in", "finally", "we achieved", "improved", "reduced", "increased",
        "saved", "delivered", "resolved", "success", "outcome", "learned", "the result",
    ),
}


def _contains_any(text: str, cues: Iterable[str]) -> bool:
    return any(cue in text for cue in cues)


def check_star_structure(answer: str) -> dict:
    """Heuristically detect Situation, Task, Action, Result components."""
    normalized = _normalize(answer or "")
    components = {
        component: _contains_any(normalized, cues)
        for component, cues in _STAR_CUES.items()
    }
    present = [name for name, found in components.items() if found]
    missing = [name for name, found in components.items() if not found]
    return {
        "tool": "check_star_structure",
        "components": components,
        "present": present,
        "missing": missing,
        "coverage": round((len(present) / 4) * 100),
        "is_complete": len(missing) == 0,
    }


def score_relevance(question: str, answer: str, expected_keywords: list[str]) -> dict:
    """Score answer relevance by expected concepts present in the response."""
    normalized_answer = _normalize(answer or "")
    matched: list[str] = []
    missing: list[str] = []
    for keyword in expected_keywords:
        if _term_pattern(keyword).search(normalized_answer):
            matched.append(keyword)
        else:
            missing.append(keyword)

    total = len(expected_keywords)
    score = round((len(matched) / total) * 100) if total else 0
    return {
        "tool": "score_relevance",
        "question": question,
        "score": score,
        "matched_concepts": matched,
        "missing_concepts": missing,
        "matched_count": len(matched),
        "expected_count": total,
    }
