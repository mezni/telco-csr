import json

import audit_log
import ticket_classifier
from agent import process_ticket
from approval import decide_approval


TICKET = "My order #4821 has not arrived."

VALID_CLASSIFICATION = {
    "category": "order_status",
    "order_id": 4821,
    "needs_order_lookup": True,
}


def fake_inference(response):
    return {
        "response": response,
        "model": "test-model",
        "latency_ms": 100,
        "input_tokens": 20,
        "output_tokens": 15,
    }


def configure_test_database(tmp_path, monkeypatch):
    """Use an isolated database for each integration test."""
    monkeypatch.setattr(
        audit_log,
        "DB_PATH",
        tmp_path / "audit.db",
    )


def test_complete_workflow_with_approval(tmp_path, monkeypatch):
    configure_test_database(tmp_path, monkeypatch)

    monkeypatch.setattr(
        ticket_classifier,
        "run_inference",
        lambda *args, **kwargs: fake_inference(json.dumps(VALID_CLASSIFICATION)),
    )

    recommendation = process_ticket(
        ticket=TICKET,
        model="test-model",
        ticket_id="TICKET-001",
    )

    assert recommendation["status"] == "pending_approval"

    final_result = decide_approval(
        recommendation,
        decision="approve",
        reviewer="reviewer-1",
    )

    assert final_result["status"] == "approved"

    events = audit_log.list_events(ticket_id="TICKET-001")
    event_types = {event["event_type"] for event in events}

    assert "classification_succeeded" in event_types
    assert "approval_granted" in event_types
    assert len(events) == 2


def test_complete_workflow_with_rejection(tmp_path, monkeypatch):
    configure_test_database(tmp_path, monkeypatch)

    monkeypatch.setattr(
        ticket_classifier,
        "run_inference",
        lambda *args, **kwargs: fake_inference(json.dumps(VALID_CLASSIFICATION)),
    )

    recommendation = process_ticket(
        ticket=TICKET,
        model="test-model",
        ticket_id="TICKET-002",
    )

    final_result = decide_approval(
        recommendation,
        decision="reject",
        reviewer="reviewer-2",
    )

    assert final_result["status"] == "rejected"

    events = audit_log.list_events(ticket_id="TICKET-002")
    event_types = {event["event_type"] for event in events}

    assert "classification_succeeded" in event_types
    assert "approval_rejected" in event_types
    assert len(events) == 2


def test_invalid_model_output_requires_manual_review(
    tmp_path,
    monkeypatch,
):
    configure_test_database(tmp_path, monkeypatch)

    monkeypatch.setattr(
        ticket_classifier,
        "run_inference",
        lambda *args, **kwargs: fake_inference("not valid JSON"),
    )

    result = process_ticket(
        ticket=TICKET,
        model="test-model",
        max_attempts=2,
        ticket_id="TICKET-003",
    )

    assert result["status"] == "needs_review"
    assert result["classification"] is None

    events = audit_log.list_events(ticket_id="TICKET-003")

    assert len(events) == 1
    assert events[0]["event_type"] == "classification_failed"
    assert events[0]["details"]["attempt_count"] == 2
