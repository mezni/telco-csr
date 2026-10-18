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
def test_valid_response_returns_classification(mock_inference):
    mock_inference.return_value = fake_inference(json.dumps(VALID_RESPONSE))

    result = classify_ticket(
        "My order #4821 has not arrived.",
        model="test-model",
    )

    assert result["status"] == "success"
    assert result["classification"] == VALID_RESPONSE
    assert result["error"] is None
    mock_inference.assert_called_once()


@patch("ticket_classifier.run_inference")
def test_malformed_json_returns_invalid_output(mock_inference):
    mock_inference.return_value = fake_inference("This is not JSON")

    result = classify_ticket("My order is late.", "test-model")

    assert result["status"] == "invalid_output"
    assert result["classification"] is None
    assert "valid JSON" in result["error"]


@patch("ticket_classifier.run_inference")
def test_invalid_category_returns_invalid_output(mock_inference):
    response = {
        **VALID_RESPONSE,
        "category": "unknown_category",
    }
    mock_inference.return_value = fake_inference(json.dumps(response))

    result = classify_ticket("Help with my order.", "test-model")

    assert result["status"] == "invalid_output"
    assert result["classification"] is None


@patch("ticket_classifier.run_inference")
def test_inference_failure_is_reported(mock_inference):
    mock_inference.side_effect = RuntimeError("Provider unavailable")

    result = classify_ticket("My order is late.", "test-model")

    assert result["status"] == "inference_error"
    assert result["classification"] is None
    assert "Inference failed" in result["error"]


@patch("ticket_classifier.run_inference")
def test_empty_ticket_is_rejected_without_calling_llm(mock_inference):
    result = classify_ticket("   ", "test-model")

    assert result["status"] == "invalid_input"
    assert result["classification"] is None
    mock_inference.assert_not_called()
