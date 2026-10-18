# tests/test_llm_service.py

from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError

import llm_service
from config import Settings
from errors import InferenceError


def make_response(text: str = "test response"):
    """Build a fake successful Responses API response."""
    return SimpleNamespace(
        output_text=text,
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
        ),
    )


class FakeResponses:
    """Mock the OpenAI Responses API."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        outcome = self.outcomes.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


class FakeClient:
    """Mock the OpenAI client."""

    def __init__(self, outcomes):
        self.responses = FakeResponses(outcomes)


def connection_error():
    request = httpx.Request(
        "GET",
        "https://example.com",
    )
    return APIConnectionError(request=request)


def timeout_error():
    request = httpx.Request(
        "POST",
        "https://example.com",
    )
    return APITimeoutError(request=request)


def status_error(status_code: int):
    request = httpx.Request(
        "POST",
        "https://example.com",
    )
    response = httpx.Response(
        status_code,
        request=request,
    )

    return APIStatusError(
        "Provider error",
        response=response,
        body=None,
    )


@pytest.fixture
def setup_provider(monkeypatch):
    """Provide test settings, fake clients, and captured sleep calls."""
    settings = Settings(
        openai_api_key="test-key",
        model="test-model",
        timeout_seconds=12.0,
        max_attempts=3,
    )

    monkeypatch.setattr(
        llm_service,
        "load_settings",
        lambda: settings,
    )

    sleep_calls = []

    monkeypatch.setattr(
        llm_service.time,
        "sleep",
        sleep_calls.append,
    )

    def install_client(outcomes):
        client = FakeClient(outcomes)
        constructor_calls = []

        def fake_openai(**kwargs):
            constructor_calls.append(kwargs)
            return client

        monkeypatch.setattr(
            llm_service,
            "OpenAI",
            fake_openai,
        )

        return client, constructor_calls

    return install_client, sleep_calls


def test_success_on_first_attempt(setup_provider):
    install_client, sleep_calls = setup_provider
    client, constructor_calls = install_client([make_response()])

    result = llm_service.run_inference(
        "Test ticket",
        model="test-model",
        system_prompt="Classify the ticket",
    )

    assert result["response"] == "test response"
    assert result["model"] == "test-model"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 5
    assert result["provider_attempts"] == 1

    assert len(client.responses.calls) == 1
    assert sleep_calls == []

    assert constructor_calls[0]["api_key"] == "test-key"
    assert constructor_calls[0]["timeout"] == 12.0
    assert constructor_calls[0]["max_retries"] == 0

    request = client.responses.calls[0]
    assert request["input"] == "Test ticket"
    assert request["instructions"] == "Classify the ticket"


def test_uses_configured_model_when_model_is_omitted(
    setup_provider,
):
    install_client, _ = setup_provider
    client, _ = install_client([make_response()])

    result = llm_service.run_inference("Test ticket")

    assert result["model"] == "test-model"
    assert client.responses.calls[0]["model"] == "test-model"


def test_transient_connection_error_then_success(
    setup_provider,
):
    install_client, sleep_calls = setup_provider
    client, _ = install_client(
        [
            connection_error(),
            make_response("recovered"),
        ]
    )

    result = llm_service.run_inference(
        "Test ticket",
        model="test-model",
    )

    assert result["response"] == "recovered"
    assert result["provider_attempts"] == 2
    assert len(client.responses.calls) == 2
    assert sleep_calls == [1]


def test_timeout_error_then_success(setup_provider):
    install_client, sleep_calls = setup_provider
    client, _ = install_client(
        [
            timeout_error(),
            make_response("recovered"),
        ]
    )

    result = llm_service.run_inference(
        "Test ticket",
        model="test-model",
    )

    assert result["response"] == "recovered"
    assert result["provider_attempts"] == 2
    assert len(client.responses.calls) == 2
    assert sleep_calls == [1]


@pytest.mark.parametrize("status_code", [408, 409, 429, 500, 502, 503, 504])
def test_transient_http_status_is_retried(
    setup_provider,
    status_code,
):
    install_client, sleep_calls = setup_provider
    client, _ = install_client(
        [
            status_error(status_code),
            make_response("recovered"),
        ]
    )

    result = llm_service.run_inference(
        "Test ticket",
        model="test-model",
    )

    assert result["response"] == "recovered"
    assert result["provider_attempts"] == 2
    assert len(client.responses.calls) == 2
    assert sleep_calls == [1]


def test_permanent_http_error_is_not_retried(
    setup_provider,
):
    install_client, sleep_calls = setup_provider
    client, _ = install_client([status_error(401)])

    with pytest.raises(InferenceError) as exc_info:
        llm_service.run_inference(
            "Test ticket",
            model="test-model",
        )

    error = exc_info.value

    assert error.retryable is False
    assert error.attempts == 1
    assert error.status_code == 401
    assert len(client.responses.calls) == 1
    assert sleep_calls == []


def test_transient_errors_exhaust_retry_budget(
    setup_provider,
):
    install_client, sleep_calls = setup_provider
    client, _ = install_client(
        [
            connection_error(),
            connection_error(),
            connection_error(),
        ]
    )

    with pytest.raises(InferenceError) as exc_info:
        llm_service.run_inference(
            "Test ticket",
            model="test-model",
        )

    error = exc_info.value

    assert error.retryable is True
    assert error.attempts == 3
    assert len(client.responses.calls) == 3
    assert sleep_calls == [1, 2]


def test_backoff_is_capped_at_four_seconds(
    setup_provider,
):
    install_client, sleep_calls = setup_provider
    client, _ = install_client(
        [
            connection_error(),
            connection_error(),
            connection_error(),
            connection_error(),
            make_response("recovered"),
        ]
    )

    # Use five attempts to exercise the backoff cap.
    original_settings = llm_service.load_settings()
    test_settings = Settings(
        openai_api_key=original_settings.openai_api_key,
        model=original_settings.model,
        timeout_seconds=original_settings.timeout_seconds,
        max_attempts=5,
    )

    # Replace the fixture settings for this test.
    # load_settings is patched by the fixture.
    llm_service.load_settings = lambda: test_settings

    try:
        result = llm_service.run_inference(
            "Test ticket",
            model="test-model",
        )
    finally:
        # pytest's monkeypatch fixture restores patches after the test;
        # this local replacement is avoided in normal production code.
        pass

    assert result["response"] == "recovered"
    assert len(client.responses.calls) == 5
    assert sleep_calls == [1, 2, 4, 4]
