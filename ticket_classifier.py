# ticket_classifier.py

import json
from typing import Any

from config import load_settings
from errors import InferenceError
from execution_budget import ExecutionBudget
from llm_service import run_inference
from ticket_schema import validate_classification

CLASSIFIER_SYSTEM_PROMPT = """
Classify the support ticket.

Return only a JSON object with exactly these fields:
- category: order_status, billing, technical_support, or other
- order_id: a positive integer or null
- needs_order_lookup: a boolean

Do not invent an order ID. Use null when no order ID is present.
Do not include Markdown or explanatory text.
"""


def classify_ticket(
    ticket: str,
    model: str | None = None,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Classify a ticket using a shared inference budget."""
    if not isinstance(ticket, str) or not ticket.strip():
        return {
            "status": "invalid_input",
            "classification": None,
            "error": "Ticket must be a non-empty string.",
            "raw_response": None,
            "attempt_count": 0,
        }

    if (
        isinstance(max_attempts, bool)
        or not isinstance(max_attempts, int)
        or max_attempts < 1
    ):
        return {
            "status": "invalid_input",
            "classification": None,
            "error": "max_attempts must be a positive integer.",
            "raw_response": None,
            "attempt_count": 0,
        }

    try:
        settings = load_settings()

        # One budget is shared across all model-output attempts.
        budget = ExecutionBudget(
            max_requests=settings.max_attempts,
            deadline_seconds=settings.deadline_seconds,
        )
    except ValueError as exc:
        return {
            "status": "invalid_input",
            "classification": None,
            "error": str(exc),
            "raw_response": None,
            "attempt_count": 0,
        }

    last_error = "The model returned invalid output."
    last_raw_response = None
    attempts_made = 0

    for attempt in range(1, max_attempts + 1):
        attempts_made = attempt
        try:
            inference = run_inference(
                ticket,
                model=model or settings.model,
                system_prompt=CLASSIFIER_SYSTEM_PROMPT,
                budget=budget,
            )

        except InferenceError as exc:
            return {
                "status": "inference_error",
                "classification": None,
                "error": str(exc),
                "raw_response": None,
                "attempt_count": attempt,
                "provider_attempts": exc.attempts,
                "retryable": exc.retryable,
                "status_code": exc.status_code,
            }

        except RuntimeError:
            # Transient provider failures are retried within the attempt budget.
            last_error = "Temporary provider failure."
            if budget.remaining_seconds <= 0:
                break
            continue

        except Exception:  # noqa: BLE001
            # Do not blindly retry unexpected programming or provider errors.
            return {
                "status": "inference_error",
                "classification": None,
                "error": "An unexpected inference error occurred.",
                "raw_response": None,
                "attempt_count": attempt,
                "provider_attempts": budget.requests_used,
                "retryable": False,
            }

        raw_response = inference.get("response")
        last_raw_response = raw_response

        try:
            if not isinstance(raw_response, str):
                raise ValueError("Model output must be a string.")

            parsed = json.loads(raw_response)
            classification = validate_classification(parsed)

        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            last_error = str(exc)

            # Do not begin another attempt after the deadline or budget expires.
            if budget.remaining_seconds <= 0:
                last_error = "Execution deadline exceeded."
                break

            if budget.requests_remaining <= 0:
                last_error = "Provider request budget exhausted."
                break

            continue

        return {
            "status": "success",
            "classification": classification.to_dict(),
            "error": None,
            "raw_response": raw_response,
            "model": inference.get("model", model or settings.model),
            "latency_ms": inference.get("latency_ms"),
            "input_tokens": inference.get("input_tokens"),
            "output_tokens": inference.get("output_tokens"),
            "provider_attempts": budget.requests_used,
            "attempt_count": attempt,
        }

    return {
        "status": "invalid_output",
        "classification": None,
        "error": last_error,
        "raw_response": last_raw_response,
        "attempt_count": attempts_made,
        "provider_attempts": budget.requests_used,
    }
