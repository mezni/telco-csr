import json

import ticket_classifier
from errors import InferenceError

VALID_CLASSIFICATION = {
    "category": "order_status",
    "order_id": 4821,
    "needs_order_lookup": True,
}


def test_provider_failure_is_not_retried_by_classifier(monkeypatch):
    calls = 0

    def failing_inference(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise InferenceError(
            "Provider unavailable.",
            retryable=True,
            attempts=3,
        )

    monkeypatch.setattr(
        ticket_classifier,
        "run_inference",
        failing_inference,
    )

    result = ticket_classifier.classify_ticket(
        ticket="My order #4821 has not arrived.",
        model="test-model",
        max_attempts=3,
    )

    assert result["status"] == "inference_error"
    assert result["retryable"] is True
    assert result["provider_attempts"] == 3
    assert calls == 1


def test_permanent_provider_error_is_not_retried(monkeypatch):
    calls = 0

    def failing_inference(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise InferenceError(
            "The model provider rejected the request.",
            retryable=False,
            attempts=1,
            status_code=401,
        )

    monkeypatch.setattr(
        ticket_classifier,
        "run_inference",
        failing_inference,
    )

    result = ticket_classifier.classify_ticket(
        ticket="My order #4821 has not arrived.",
        model="test-model",
        max_attempts=3,
    )

    assert result["status"] == "inference_error"
    assert result["retryable"] is False
    assert result["status_code"] == 401
    assert calls == 1


def test_invalid_model_output_is_retried(monkeypatch):
    responses = iter(
        [
            "not valid JSON",
            json.dumps(VALID_CLASSIFICATION),
        ]
    )
    calls = 0

    def fake_inference(*args, **kwargs):
        nonlocal calls
        calls += 1
        return {
            "response": next(responses),
            "model": "test-model",
            "latency_ms": 100,
            "input_tokens": 20,
            "output_tokens": 15,
        }

    monkeypatch.setattr(
        ticket_classifier,
        "run_inference",
        fake_inference,
    )

    result = ticket_classifier.classify_ticket(
        ticket="My order #4821 has not arrived.",
        model="test-model",
        max_attempts=3,
    )

    assert result["status"] == "success"
    assert result["classification"] == VALID_CLASSIFICATION
    assert result["attempt_count"] == 2
    assert calls == 2


def test_invalid_input_does_not_call_provider(monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("Provider must not be called.")

    monkeypatch.setattr(
        ticket_classifier,
        "run_inference",
        unexpected_call,
    )

    result = ticket_classifier.classify_ticket(
        ticket="   ",
        model="test-model",
    )

    assert result["status"] == "invalid_input"
    assert result["attempt_count"] == 0
