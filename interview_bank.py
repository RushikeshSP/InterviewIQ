"""Interview question bank used by the InterviewIQ browser application."""

QUESTIONS = [
    {
        "id": "q1",
        "category": "behavioral",
        "question": "Tell me about a time you had to solve a difficult technical problem under a tight deadline.",
        "expected_keywords": [
            "technical problem",
            "deadline",
            "root cause",
            "debug",
            "action",
            "solution",
            "result",
        ],
    },
    {
        "id": "q2",
        "category": "technical",
        "question": "What is the difference between a process and a thread, and when would you use each?",
        "expected_keywords": [
            "process",
            "thread",
            "memory",
            "address space",
            "context switch",
            "concurrency",
            "parallelism",
        ],
    },
    {
        "id": "q3",
        "category": "behavioral",
        "question": "Describe a situation where you disagreed with a teammate and how you handled it.",
        "expected_keywords": [
            "disagreement",
            "teammate",
            "communication",
            "discussion",
            "action",
            "resolution",
            "result",
        ],
    },
    {
        "id": "q4",
        "category": "technical",
        "question": "How would you design a web scraper that can run reliably at scale?",
        "expected_keywords": [
            "queue",
            "workers",
            "retry",
            "proxy",
            "rate limit",
            "monitoring",
            "deduplication",
            "storage",
        ],
    },
    {
        "id": "q5",
        "category": "behavioral",
        "question": "Tell me about a project that did not go as planned. What did you learn?",
        "expected_keywords": [
            "project",
            "problem",
            "impact",
            "action",
            "lesson",
            "improvement",
            "result",
        ],
    },
    {
        "id": "q6",
        "category": "technical",
        "question": "Explain how an index improves database query performance and what trade-offs it introduces.",
        "expected_keywords": [
            "index",
            "query",
            "lookup",
            "b-tree",
            "read",
            "write",
            "storage",
        ],
    },
]


def get_question(index: int) -> dict:
    if not 0 <= index < len(QUESTIONS):
        raise IndexError("Question index out of range")
    return QUESTIONS[index]
