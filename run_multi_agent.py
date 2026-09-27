"""Optional bonus multi-agent loop."""

from agent import InterviewSession, evaluate_answer
from interview_bank import QUESTIONS
from interviewer_agent import choose_next_category


def main() -> None:
    session = InterviewSession()
    q = QUESTIONS[0]
    answer = input(f"{q['question']}\n\nAnswer: ")
    record = evaluate_answer(session, q, answer)
    print("\nEvaluator feedback:", record.feedback)
    print("Next category selected by Interviewer:", choose_next_category(session))


if __name__ == "__main__":
    main()
