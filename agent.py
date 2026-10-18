from typing import Any
from uuid import uuid4

from audit_log import log_event
from observability import log_agent_event
from ticket_classifier import classify_ticket


def process_ticket(
    ticket: str,
    model: str,
    max_attempts: int = 3,
    ticket_id: str | None = None,
) -> dict[str, Any]:
    """Classify a ticket and prepare the recommendation for human approval."""
    ticket_id = ticket_id or str(uuid4())

    log_agent_event(
        "ticket_processing_started",
        ticket_id,
        model=model,
    )

    classification_result = classify_ticket(
        ticket=ticket,
        model=model,
        max_attempts=max_attempts,
    )

    attempt_count = classification_result.get("attempt_count", 0)

    if classification_result["status"] != "success":
        error = classification_result.get("error")
        failure_status = classification_result["status"]

        log_event(
            ticket_id=ticket_id,
            event_type="classification_failed",
            details={
                "status": failure_status,
                "error": error,
                "attempt_count": attempt_count,
            },
        )

        log_agent_event(
            "classification_failed",
            ticket_id,
            status=failure_status,
            attempt_count=attempt_count,
        )

        return {
            "status": "needs_review",
            "ticket_id": ticket_id,
            "ticket": ticket,
            "classification": None,
            "decision": "manual_review_required",
            "error": error,
            "attempt_count": attempt_count,
        }

    classification = classification_result["classification"]
    latency_ms = classification_result.get("latency_ms")
    resolved_model = classification_result.get("model", model)

    log_event(
        ticket_id=ticket_id,
        event_type="classification_succeeded",
        details={
            "classification": classification,
            "attempt_count": attempt_count,
            "model": resolved_model,
            "latency_ms": latency_ms,
        },
    )

    log_agent_event(
        "classification_succeeded",
        ticket_id,
        attempt_count=attempt_count,
        latency_ms=latency_ms,
    )

    return {
        "status": "pending_approval",
        "ticket_id": ticket_id,
        "ticket": ticket,
        "classification": classification,
        "decision": "awaiting_human_approval",
        "error": None,
        "attempt_count": attempt_count,
        "model": resolved_model,
        "latency_ms": latency_ms,
        "input_tokens": classification_result.get("input_tokens"),
        "output_tokens": classification_result.get("output_tokens"),
    }
