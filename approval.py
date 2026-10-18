from typing import Any
from audit_log import log_event

VALID_DECISIONS = {"approve", "reject"}


def decide_approval(
    agent_result: dict[str, Any],
    decision: str,
    reviewer: str,
) -> dict[str, Any]:
    """Record a human decision about a pending recommendation."""

    if decision not in VALID_DECISIONS:
        raise ValueError(
            f"Decision must be one of: {sorted(VALID_DECISIONS)}"
        )

    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Reviewer must be a non-empty string.")

    if agent_result.get("status") != "pending_approval":
        raise ValueError(
            "Only recommendations pending approval can be decided."
        )

    classification = agent_result.get("classification")

    if not isinstance(classification, dict):
        raise TypeError("A valid classification is required for approval.")

    if decision == "approve":
        status = "approved"
    else:
        status = "rejected"

    log_event(
        ticket_id=agent_result["ticket_id"],
        event_type=(
            "approval_granted"
            if decision == "approve"
            else "approval_rejected"
        ),
        details={
            "reviewer": reviewer.strip(),
            "decision": decision,
        },
    )

    return {
        **agent_result,
        "status": status,
        "decision": decision,
        "reviewer": reviewer.strip(),
    }
