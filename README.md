# Telco Customer Support Agent

An AI-assisted support ticket triage agent with a Streamlit evaluation lab for
prompt engineering, LLM experiment tracking, and human-in-the-loop approval.

The project has two entry points:

- **`app.py`** — a multi-page Streamlit lab for running LLM inference,
  comparing prompts, scoring accuracy against a labeled dataset, and
  inspecting experiment history, cost, and regression reports.
- **`cli.py`** — a command-line triage agent that classifies a ticket with a
  validated schema, records audit events, and requests a human approval
  decision before acting.

## Features

### Evaluation lab (Streamlit)

| Page | Purpose |
| --- | --- |
| `1_LLM_Inference` | Run a single inference request and inspect latency/token metrics |
| `2_Prompt_Experiments` | A/B compare two system prompts on one ticket |
| `3_Evaluation` | Score a prompt against the full labeled dataset |
| `4_Prompt_Score_Comparison` | Evaluate two prompts on all tickets and persist both runs |
| `5_Experiment_History` | Browse stored experiments in SQLite |
| `6_Experiment_Dashboard` | Visualize experiment history |
| `7_Regression_Checker` | Compare experiment versions and detect regressions |
| `8_Evaluation_Gates` | Check experiments against configurable quality gates |
| `9_Error_Analysis` | Per-category error breakdown |
| `10_Cost_Performance` | Cost and performance analysis of experiments |
| `11_Evaluation_Report` | Consolidated evaluation report |

### Triage agent (CLI)

- **Validated classification schema** — model output is parsed and validated
  (`ticket_schema.py`) into a typed result; malformed output is never trusted.
- **Bounded retries** — malformed JSON and transient provider failures are
  retried up to a configured attempt limit.
- **Shared inference budget** — every classification run is bounded by a
  maximum request count and a wall-clock deadline (`execution_budget.py`).
- **Human approval** — classifications are recommendations only; a reviewer
  must approve or reject them (`approval.py`).
- **Audit log** — classification and approval events are persisted to SQLite
  (`audit_log.py`).
- **Operational metrics** — success rate, latency, and attempt statistics are
  derived from the audit log (`metrics.py`).
- **Reproducibility metadata** — prompt fingerprints, dataset fingerprints,
  and manifests are recorded for every experiment (`reproducibility.py`).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An OpenAI API key

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY and OPENAI_MODEL
```

| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key used for all model requests | — (required) |
| `OPENAI_MODEL` | Default model identifier | — (required) |
| `LLM_TIMEOUT_SECONDS` | Per-request timeout | `30` |
| `LLM_MAX_ATTEMPTS` | Shared request budget per classification | `3` |
| `LLM_DEADLINE_SECONDS` | Wall-clock deadline per classification | `60` |

## Usage

### Streamlit lab

```bash
uv run streamlit run app.py
```

### Triage CLI

```bash
# Classify a ticket, then approve or reject the recommendation
uv run python cli.py triage \
  --ticket "My order #4821 has not arrived." \
  --model gpt-6-luna \
  --ticket-id TICKET-001

# Show recent audit events (optionally filtered by ticket)
uv run python cli.py history --limit 20
uv run python cli.py history --ticket-id TICKET-001

# Show operational metrics
uv run python cli.py metrics
```

Exit codes for `triage`: `0` on success, `1` when classification failed and
manual review is required, `2` on invalid input.

## Development

```bash
# Run the test suite
uv run pytest

# Run a single test file
uv run pytest tests/test_ticket_schema.py

# Lint
uv run ruff check .

# Apply safe lint fixes
uv run ruff check --fix .
```

## Project structure

```
.
├── app.py                  # Streamlit entry point
├── cli.py                  # CLI entry point (triage/history/metrics)
├── agent.py                # Ticket processing orchestrator
├── approval.py             # Human approval workflow
├── audit_log.py            # SQLite audit event store
├── config.py               # Environment settings
├── ticket_classifier.py    # LLM classification with bounded retries
├── ticket_schema.py        # Classification schema validation
├── execution_budget.py     # Request count + deadline budget
├── llm_service.py          # OpenAI client wrapper
├── errors.py               # InferenceError with retry metadata
├── metrics.py              # Operational metrics from audit events
├── reproducibility.py      # Prompt/dataset fingerprints, manifests
├── prompt_evaluation.py    # Prompt scoring against labeled dataset
├── evaluator.py            # Field-level accuracy scoring
├── experiment_store.py     # Experiment history (SQLite)
├── evaluation_report.py    # Consolidated report generation
├── pages/                  # Streamlit lab pages (1_–11_)
├── tests/                  # pytest suite (131 tests)
└── data/
    ├── eval_tickets.json   # Labeled evaluation dataset
    ├── experiments.db      # Experiment history database
    └── audit.db            # Audit event database
```

## Data & storage

SQLite databases under `data/` are created automatically on first use:

- `experiments.db` — one row per prompt evaluation run, including accuracy,
  latency, token usage, and per-ticket details.
- `audit.db` — classification and approval events for the triage agent.

Both are safe to delete; they are rebuilt on demand.

## License

Licensed under the [Apache License 2.0](LICENSE).
