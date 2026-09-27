"""Optional bonus interviewer agent that chooses the next question category."""

from __future__ import annotations

from agent import InterviewSession


def choose_next_category(session: InterviewSession) -> str:
    if not session.records:
        return "behavioral"

    categories = {"behavioral", "technical"}
    recent = [record.category for record in session.records[-3:]]
    if recent and recent[-1] == "behavioral":
        categories.discard("behavioral")
    elif recent and recent[-1] == "technical":
        categories.discard("technical")

    weakest = session.weakest_record()
    if weakest and weakest.category in categories:
        return weakest.category
    return next(iter(categories), "technical")
