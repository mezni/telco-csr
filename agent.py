from typing import Any
from uuid import uuid4

from audit_log import log_event
from ticket_classifier import classify_ticket


def process_ticket(
    ticket: str,
    model: str,
    max_attempts: int = 3,
    ticket_id: str | None = None,
) -> dict[str, Any]:
    """Classify a ticket and record the outcome."""

    ticket_id = ticket_id or str(uuid4())

    classification_result = classify_ticket(
        ticket=ticket,
        model=model,
        max_attempts=max_attempts,
    )

    if classification_result["status"] != "success":
        log_event(
            ticket_id=ticket_id,
            event_type="classification_failed",
            details={
                "status": classification_result["status"],
                "error": classification_result.get("error"),
                "attempt_count": classification_result.get(
                    "attempt_count", 0
                ),
            },
        )

        return {
            "status": "needs_review",
            "ticket_id": ticket_id,
            "ticket": ticket,
            "classification": None,
            "decision": "manual_review_required",
            "error": classification_result.get("error"),
            "attempt_count": classification_result.get(
                "attempt_count", 0
            ),
        }

    classification = classification_result["classification"]

    log_event(
        ticket_id=ticket_id,
        event_type="classification_succeeded",
        details={
            "classification": classification,
            "attempt_count": classification_result["attempt_count"],
            "model": classification_result.get("model", model),
        },
    )

    return {
        "status": "pending_approval",
        "ticket_id": ticket_id,
        "ticket": ticket,
        "classification": classification,
        "decision": "awaiting_human_approval",
        "error": None,
        "attempt_count": classification_result["attempt_count"],
        "model": classification_result.get("model", model),
        "latency_ms": classification_result.get("latency_ms"),
        "input_tokens": classification_result.get("input_tokens"),
        "output_tokens": classification_result.get("output_tokens"),
    }
