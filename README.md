# InterviewIQ

InterviewIQ is an AI-powered mock-interview coach built around a tool-calling evaluator, deterministic scoring tools, session memory, aggregated reporting, and a Gradio browser interface.

## Architecture

```text
Candidate answer
      |
      v
Evaluator Agent (Groq/OpenAI-compatible API)
      |
      +--> detect_filler_words
      +--> check_star_structure (behavioral)
      +--> score_relevance
      |
      v
Structured evaluation + encouraging feedback
      |
      v
InterviewSession memory
      |
      +--> Live scorecard
      +--> Coach / meta-questions
      +--> Final aggregated report
```

The three evaluators are intentionally deterministic and return dictionaries. The LLM chooses relevant tools and converts the returned data into feedback. A local fallback mode is included so the project can be tested without an API key.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GROQ_API_KEY
```

Groq is configured through the OpenAI-compatible API endpoint `https://api.groq.com/openai/v1`.

## Run the checks

```bash
python -m pytest -q
python memory_check.py
```

## Run the CLI

```bash
python main.py
```

## Run the Gradio application

```bash
python app.py
```

Then open the local URL shown by Gradio.

## Optional bonus

```bash
python run_multi_agent.py
```

`interviewer_agent.py` demonstrates a simple second agent that chooses the next question category from session performance.

## Project structure

| File | Purpose |
|---|---|
| `tools.py` | Three rule-based evaluation functions |
| `agent.py` | Tool-calling agent, session memory, coach, final aggregation |
| `interview_bank.py` | Interview questions and expected concepts |
| `memory_check.py` | Required memory/weakest-area verification |
| `app.py` | Gradio browser UI |
| `main.py` | CLI smoke runner |
| `interviewer_agent.py` | Optional bonus interviewer agent |
| `run_multi_agent.py` | Optional bonus orchestrator demo |
| `test_tools.py` | Unit tests for deterministic tools |

## Notes on the starter kit

The supplied starter archive contained the environment template, README, requirements, `.gitignore`, and problem statement, but not the Python helper files referenced by the README. This implementation therefore supplies those missing files while preserving the required milestone flow.
