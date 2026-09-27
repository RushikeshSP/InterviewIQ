"""CLI smoke runner for InterviewIQ."""

from agent import InterviewSession, evaluate_answer
from interview_bank import QUESTIONS


def main() -> None:
    session = InterviewSession()
    question = QUESTIONS[0]
    print(f"Question: {question['question']}")
    answer = input("Answer: ").strip()
    record = evaluate_answer(session, question, answer)
    print("\nTools used:", ", ".join(record.tools_used))
    print("Relevance:", record.relevance_score)
    print("Feedback:", record.feedback)


if __name__ == "__main__":
    main()
