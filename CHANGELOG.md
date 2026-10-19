# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Ignore `TRY004` in the Ruff configuration so validation errors stay
  `ValueError`, matching the test suite contract.

### Fixed

- Retry transient `RuntimeError` provider failures within the attempt budget
  instead of aborting with `inference_error`.
- Report the real number of attempts made when classification exhausts the
  attempt budget (`attempts_made` instead of the request counter, which is
  `0` when inference is mocked or free).
- Record approval audit events under the correct ticket identifier by reading
  `ticket_id` (falling back to `ticket`) instead of a hard-coded key lookup
  that raised `KeyError`.
- Call `decide_approval` with a positional recommendation so the recorded
  call matches the CLI contract.
- Reject `inf` and `nan` execution deadlines in `ExecutionBudget` so invalid
  deadlines always raise `ValueError`.
- Load environment variables once at import time in `config.py` so
  `load_settings()` no longer re-reads `.env` and overrides a removed
  `OPENAI_API_KEY`.
- Remove a duplicate, shadowed `test_success_waits_for_human_approval`
  definition that never ran (Ruff `F811`).

### Changed

- Clean up import ordering and use the `datetime.UTC` alias across the
  codebase; catch specific OpenAI/IO exception types instead of blind
  `Exception` handlers in the Streamlit pages.

## [0.1.0] - 2026-10-18

Initial release: an evaluation lab and a human-in-the-loop ticket triage
agent.

### Added

- **Project scaffolding** with `uv`, `pytest`, and `ruff`.
- **Rule-based baseline classifier** and a first Streamlit demo page that
  measures local execution time.
- **LLM inference** — first real model call with latency and token metric
  capture, plus a Streamlit page to inspect the results.
- **Evaluation dataset** — labeled support tickets with field-level accuracy
  scoring (category, order ID, lookup flag) and dataset validation.
- **Prompt experiments** — A/B comparison of two system prompts and scoring
  of multiple prompts against the full dataset.
- **Experiment store** — persistent experiment history in SQLite with prompt
  name, version, and SHA-256 prompt fingerprints.
- **Experiment visualization** — history, dashboard, and regression-checker
  Streamlit pages.
- **Evaluation gates** — configurable accuracy, latency, and JSON-validity
  thresholds for accepting an experiment.
- **Error analysis** — per-category breakdown of incorrect predictions.
- **Reproducibility metadata** — prompt fingerprints, dataset fingerprints,
  and manifests recorded for each evaluation run.
- **Cost and performance analysis** — token cost estimates plus latency
  statistics (mean/P95) per experiment.
- **Evaluation report** — consolidated Markdown report combining accuracy,
  performance, gates, and error analysis.
- **Validated ticket classification schema** — untrusted model output is
  parsed and validated into a typed `TicketClassification`.
- **Bounded retries** — malformed JSON and provider failures retried up to a
  configured attempt limit.
- **Ticket triage agent orchestrator** that prepares recommendations for
  human approval and emits structured results.
- **Human approval workflow** — reviewers approve or reject recommendations;
  decisions are recorded without mutating the original result.
- **Audit events** — classification and approval events persisted to SQLite.
- **Triage CLI** with `triage`, `history`, and `metrics` subcommands.
- **Observability and operational metrics** — agent event logging plus
  success rate, latency, and attempt statistics derived from the audit log.
- **Production configuration** — environment-driven timeouts, retry counts,
  and deadline controls with validation.
- **Provider retry policies** — transient status codes and connection/time-out
  errors retried with capped exponential backoff; non-transient rejections
  fail fast.
- **Shared inference budget** — one request-count and wall-clock budget shared
  across all attempts of a classification run.
- **Test suite** covering the classifier, evaluation pipeline, experiment
  store, approval workflow, audit log, CLI, configuration, cost analysis,
  reproducibility, and the complete triage workflow (131 tests).

### Fixed

- Resolve Streamlit metric table serialization when rendering experiment
  comparisons.
