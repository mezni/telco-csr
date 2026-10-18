import json
from typing import Any

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
) -> dict[str, Any]:
    """Classify a support ticket and report failures explicitly."""
    if not isinstance(ticket, str) or not ticket.strip():
        return {
            "status": "invalid_input",
            "classification": None,
            "error": "Ticket must be a non-empty string.",
            "raw_response": None,
        }

    try:
        inference = run_inference(
            ticket,
            model=model,
            system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        )
    except Exception as exc:
        # Keep the error visible to the caller; don't invent a result.
        return {
            "status": "inference_error",
            "classification": None,
            "error": f"Inference failed: {exc}",
            "raw_response": None,
        }

    raw_response = inference.get("response", "")

    try:
        parsed: Any = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        return {
            "status": "invalid_output",
            "classification": None,
            "error": "The model response was not valid JSON.",
            "raw_response": raw_response,
        }

    try:
        classification: TicketClassification = validate_classification(parsed)
    except ValueError as exc:
        return {
            "status": "invalid_output",
            "classification": None,
            "error": str(exc),
            "raw_response": raw_response,
        }

    return {
        "status": "success",
        "classification": classification.to_dict(),
        "error": None,
        "raw_response": raw_response,
        "model": inference.get("model", model),
        "latency_ms": inference.get("latency_ms"),
        "input_tokens": inference.get("input_tokens"),
        "output_tokens": inference.get("output_tokens"),
    }
