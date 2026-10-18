import json
from unittest.mock import patch

from ticket_classifier import classify_ticket


VALID_RESPONSE = {
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


@patch("ticket_classifier.run_inference")
def test_retries_malformed_json_then_succeeds(mock_inference):
    mock_inference.side_effect = [
        fake_inference("not valid JSON"),
        fake_inference(json.dumps(VALID_RESPONSE)),
    ]

    result = classify_ticket(
        "My order #4821 has not arrived.",
        model="test-model",
        max_attempts=3,
    )

    assert result["status"] == "success"
    assert result["attempt_count"] == 2
    assert result["classification"] == VALID_RESPONSE
    assert mock_inference.call_count == 2


@patch("ticket_classifier.run_inference")
def test_retries_inference_exception_then_succeeds(mock_inference):
    mock_inference.side_effect = [
        RuntimeError("Temporary provider failure"),
        fake_inference(json.dumps(VALID_RESPONSE)),
    ]

    result = classify_ticket(
        "My order #4821 has not arrived.",
        model="test-model",
        max_attempts=3,
    )

    assert result["status"] == "success"
    assert result["attempt_count"] == 2
    assert mock_inference.call_count == 2


@patch("ticket_classifier.run_inference")
def test_stops_after_max_attempts(mock_inference):
    mock_inference.return_value = fake_inference("not valid JSON")

    result = classify_ticket(
        "My order is late.",
        model="test-model",
        max_attempts=2,
    )

    assert result["status"] == "invalid_output"
    assert result["classification"] is None
    assert result["attempt_count"] == 2
    assert mock_inference.call_count == 2


@patch("ticket_classifier.run_inference")
def test_success_on_first_attempt_does_not_retry(mock_inference):
    mock_inference.return_value = fake_inference(
        json.dumps(VALID_RESPONSE)
    )

    result = classify_ticket(
        "My order #4821 has not arrived.",
        model="test-model",
        max_attempts=3,
    )

    assert result["status"] == "success"
    assert result["attempt_count"] == 1
    mock_inference.assert_called_once()


def test_invalid_max_attempts_is_rejected():
    result = classify_ticket(
        "My order is late.",
        model="test-model",
        max_attempts=0,
    )

    assert result["status"] == "invalid_input"
    assert result["attempt_count"] == 0
