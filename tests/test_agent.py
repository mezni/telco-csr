from unittest.mock import patch

from agent import process_ticket

VALID_CLASSIFICATION = {
    "category": "order_status",
    "order_id": 4821,
    "needs_order_lookup": True,
}


@patch("agent.classify_ticket")
def test_success_waits_for_human_approval(mock_classifier):
    mock_classifier.return_value = {
        "status": "success",
        "classification": VALID_CLASSIFICATION,
        "error": None,
        "attempt_count": 1,
        "model": "test-model",
        "latency_ms": 100,
        "input_tokens": 20,
        "output_tokens": 15,
    }

    result = process_ticket(
        "My order #4821 has not arrived.",
        model="test-model",
    )

    assert result["status"] == "pending_approval"
    assert result["decision"] == "awaiting_human_approval"
    assert result["classification"] == VALID_CLASSIFICATION
    assert result["error"] is None


@patch("agent.classify_ticket")
def test_classification_failure_requires_manual_review(mock_classifier):
    mock_classifier.return_value = {
        "status": "invalid_output",
        "classification": None,
        "error": "The model response was not valid JSON.",
        "attempt_count": 3,
    }

    result = process_ticket(
        "My order is late.",
        model="test-model",
    )

    assert result["status"] == "needs_review"
    assert result["decision"] == "manual_review_required"
    assert result["classification"] is None
    assert result["attempt_count"] == 3
    assert "valid JSON" in result["error"]


@patch("agent.classify_ticket")
def test_orchestrator_passes_retry_limit_to_classifier(mock_classifier):
    mock_classifier.return_value = {
        "status": "success",
        "classification": VALID_CLASSIFICATION,
        "error": None,
        "attempt_count": 1,
    }

    process_ticket(
        "My order #4821 has not arrived.",
        model="test-model",
        max_attempts=5,
    )

    mock_classifier.assert_called_once_with(
        ticket="My order #4821 has not arrived.",
        model="test-model",
        max_attempts=5,
    )
