"""Gradio browser application for InterviewIQ."""

from __future__ import annotations

import gradio as gr

from agent import InterviewSession, ask_agent, evaluate_answer, generate_final_report
from interview_bank import QUESTIONS

SCORE_HEADERS = ["#", "Category", "Question", "Relevance", "Fillers", "STAR", "Feedback"]


def new_state() -> InterviewSession:
    return InterviewSession()


def scorecard_value(session: InterviewSession):
    return session.to_scorecard()


def submit_answer(answer: str, question_index: int, session: InterviewSession):
    try:
        question = QUESTIONS[question_index]
        record = evaluate_answer(session, question, answer)
        next_index = question_index + 1
        if next_index < len(QUESTIONS):
            next_question = QUESTIONS[next_index]["question"]
            next_status = f"Question {next_index + 1} of {len(QUESTIONS)}"
        else:
            next_index = question_index
            next_question = "Interview complete — use Final Report or ask the coach about your performance."
            next_status = "Interview complete"

        return (
            record.feedback,
            scorecard_value(session),
            session,
            next_index,
            next_question,
            next_status,
            "",
        )
    except Exception as exc:
        return (
            f"**Error:** {exc}",
            scorecard_value(session),
            session,
            question_index,
            QUESTIONS[question_index]["question"],
            f"Question {question_index + 1} of {len(QUESTIONS)}",
            answer,
        )


def coach_question(message: str, session: InterviewSession):
    try:
        return ask_agent(session, message), ""
    except Exception as exc:
        return f"**Error:** {exc}", message


def build_app() -> gr.Blocks:
    initial_question = QUESTIONS[0]["question"]
    with gr.Blocks(title="InterviewIQ") as demo:
        session_state = gr.State(new_state())
        question_index = gr.State(0)

        gr.Markdown(
            "# InterviewIQ\n"
            "### AI-powered mock interview coach\n"
            "Answer the question, get tool-backed feedback, track your scorecard, and ask the coach about your progress."
        )

        status = gr.Markdown(f"Question 1 of {len(QUESTIONS)}")
        current_question = gr.Markdown(f"## {initial_question}")

        with gr.Row():
            with gr.Column(scale=2):
                answer_box = gr.Textbox(
                    label="Your answer",
                    placeholder="Type your interview answer here...",
                    lines=10,
                )
                submit = gr.Button("Evaluate Answer", variant="primary")
                feedback = gr.Markdown("### Feedback\nSubmit an answer to begin.")

            with gr.Column(scale=3):
                gr.Markdown("### Live Scorecard")
                scorecard = gr.Dataframe(
                    headers=SCORE_HEADERS,
                    datatype=["number", "str", "str", "number", "number", "str", "str"],
                    value=[],
                    interactive=False,
                    wrap=True,
                )

        with gr.Row():
            coach_box = gr.Textbox(
                label="Ask the coach",
                placeholder="How am I doing so far? What should I improve?",
                lines=3,
            )
            coach_button = gr.Button("Ask Coach")

        coach_response = gr.Markdown()
        final_button = gr.Button("Generate Final Report", variant="secondary")
        final_report = gr.Markdown()
        restart_button = gr.Button("Restart Interview")

        submit.click(
            submit_answer,
            inputs=[answer_box, question_index, session_state],
            outputs=[feedback, scorecard, session_state, question_index, current_question, status, answer_box],
        )
        coach_button.click(
            coach_question,
            inputs=[coach_box, session_state],
            outputs=[coach_response, coach_box],
        )
        final_button.click(
            lambda session: generate_final_report(session),
            inputs=[session_state],
            outputs=[final_report],
        )
        restart_button.click(
            lambda: (new_state(), 0, initial_question, f"Question 1 of {len(QUESTIONS)}", [], "", ""),
            inputs=[],
            outputs=[session_state, question_index, current_question, status, scorecard, feedback, final_report],
        )

    return demo


if __name__ == "__main__":
    build_app().launch()
