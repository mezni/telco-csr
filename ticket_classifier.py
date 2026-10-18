import json
from typing import Any

from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from llm_service import run_inference
from ticket_schema import TicketClassification, validate_classification

CLASSIFIER_SYSTEM_PROMPT = """
You classify customer support tickets.

Return exactly one valid JSON object with these fields:
- category: one of "order_status", "billing",
  "technical_support", or "other"
- order_id: a positive integer if an order ID is present,
  otherwise null
- needs_order_lookup: true if checking order information
  is necessary, otherwise false

Do not include Markdown fences or explanatory text.
Do not invent an order ID.
"""


def classify_ticket(
    ticket: str,
    model: str,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Classify a ticket, retrying failures up to max_attempts."""

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

    last_status = "inference_error"
    last_error = "Classification failed."
    last_raw_response = None

    for attempt in range(1, max_attempts + 1):
        try:
            inference = run_inference(
                ticket,
                model=model,
                system_prompt=CLASSIFIER_SYSTEM_PROMPT,
            )
        except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
            last_status = "inference_error"
            last_error = f"Inference failed: {exc}"
            continue

        raw_response = inference.get("response", "")
        last_raw_response = raw_response

        try:
            parsed: Any = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            last_status = "invalid_output"
            last_error = "The model response was not valid JSON."
            continue

        try:
            classification: TicketClassification = (
                validate_classification(parsed)
            )
        except ValueError as exc:
            last_status = "invalid_output"
            last_error = str(exc)
            continue

        return {
            "status": "success",
            "classification": classification.to_dict(),
            "error": None,
            "raw_response": raw_response,
            "model": inference.get("model", model),
            "latency_ms": inference.get("latency_ms"),
            "input_tokens": inference.get("input_tokens"),
            "output_tokens": inference.get("output_tokens"),
            "attempt_count": attempt,
        }

    return {
        "status": last_status,
        "classification": None,
        "error": last_error,
        "raw_response": last_raw_response,
        "attempt_count": max_attempts,
    }
