from typing import Any

from ticket_classifier import classify_ticket


def process_ticket(
    ticket: str,
    model: str,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Orchestrate ticket classification and the next decision."""

    classification_result = classify_ticket(
        ticket=ticket,
        model=model,
        max_attempts=max_attempts,
    )

    if classification_result["status"] != "success":
        return {
            "status": "needs_review",
            "ticket": ticket,
            "classification": None,
            "decision": "manual_review_required",
            "error": classification_result.get("error"),
            "attempt_count": classification_result.get(
                "attempt_count", 0
            ),
        }

    return {
        "status": "pending_approval",
        "ticket": ticket,
        "classification": classification_result["classification"],
        "decision": "awaiting_human_approval",
        "error": None,
        "attempt_count": classification_result["attempt_count"],
        "model": classification_result.get("model", model),
        "latency_ms": classification_result.get("latency_ms"),
        "input_tokens": classification_result.get("input_tokens"),
        "output_tokens": classification_result.get("output_tokens"),
    }
