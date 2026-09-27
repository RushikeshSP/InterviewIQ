"""Verification script required by the InterviewIQ brief."""

from agent import InterviewSession, ask_agent, evaluate_answer


STRONG_QUESTION = {
    "id": "memory-strong",
    "category": "technical",
    "question": "How would you design a reliable web scraper that runs at scale?",
    "expected_keywords": ["queue", "workers", "retry", "proxy", "rate limit", "monitoring", "storage"],
}

WEAK_QUESTION = {
    "id": "memory-weak",
    "category": "technical",
    "question": "Explain database indexing and its trade-offs.",
    "expected_keywords": ["index", "query", "lookup", "b-tree", "read", "write", "storage"],
}


def main() -> None:
    session = InterviewSession()

    strong_answer = (
        "I would put URLs into a queue, run multiple workers, add retry with backoff, use proxies with rate limiting, "
        "monitor worker health, and persist crawled data to storage so failures can resume safely."
    )
    weak_answer = "I would just use a database and write queries."

    evaluate_answer(session, STRONG_QUESTION, strong_answer)
    evaluate_answer(session, WEAK_QUESTION, weak_answer)

    weakest = session.weakest_record()
    assert weakest is not None
    assert weakest.question == WEAK_QUESTION["question"], (
        "Memory check failed: weakest area was not the deliberately weak answer."
    )

    coach_response = ask_agent(session, "What's my weakest area?")
    assert WEAK_QUESTION["question"] in coach_response, (
        "Memory check failed: coach response did not use the full session history."
    )

    print("PASS: session memory and weakest-area aggregation are working.")
    print(f"Average relevance: {session.average_relevance()}/100")
    print(f"Weakest area: {weakest.question} ({weakest.relevance_score}/100)")
    print(f"Coach: {coach_response}")


if __name__ == "__main__":
    main()
