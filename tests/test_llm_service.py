
from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError, APIStatusError

import llm_service
from config import Settings


def make_response(text="test response"):
    return SimpleNamespace(
        output_text=text,
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
        ),
    )


class FakeResponses:
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
    def __init__(self, outcomes):
        self.responses = FakeResponses(outcomes)


def connection_error():
    request = httpx.Request(
        "GET",
        "https://example.com",
    )
    return APIConnectionError(request=request)


def status_error(status_code):
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
    client_settings = Settings(
        openai_api_key="test-key",
        model="test-model",
        timeout_seconds=12.0,
        max_attempts=3,
    )

    monkeypatch.setattr(
        llm_service,
        "load_settings",
        lambda: client_settings,
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
    client, constructor_calls = install_client(
        [make_response()]
    )

    result = llm_service.run_inference(
        "Test ticket",
        model="test-model",
        system_prompt="Classify the ticket",
    )

    assert result["response"] == "test response"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 5
    assert len(client.responses.calls) == 1
    assert sleep_calls == []

    assert constructor_calls[0]["timeout"] == 12.0
    assert constructor_calls[0]["max_retries"] == 0


def test_transient_error_then_success(setup_provider):
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
    assert len(client.responses.calls) == 2
    assert sleep_calls == [1]


def test_permanent_error_is_not_retried(setup_provider):
    install_client, sleep_calls = setup_provider
    client, _ = install_client(
        [status_error(401)]
    )

    with pytest.raises(APIStatusError):
        llm_service.run_inference(
            "Test ticket",
            model="test-model",
        )

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

    with pytest.raises(
        RuntimeError,
        match="failed after 3 attempts",
    ):
        llm_service.run_inference(
            "Test ticket",
            model="test-model",
        )

    assert len(client.responses.calls) == 3
    assert sleep_calls == [1, 2]

