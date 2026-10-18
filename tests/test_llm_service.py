from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from llm_service import run_inference


def test_run_inference_returns_response_and_metrics():
    fake_response = SimpleNamespace(
        output_text="Category: order_status",
        usage=SimpleNamespace(
            input_tokens=20,
            output_tokens=8,
            total_tokens=28,
        ),
    )

    fake_client = MagicMock()
    fake_client.responses.create.return_value = fake_response

    with (
        patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
        patch("llm_service.OpenAI", return_value=fake_client),
    ):
        result = run_inference(
            ticket="My order #4821 has not arrived.",
            system_prompt="Classify the ticket.",
            model="gpt-6-luna",
        )

    assert result["response"] == "Category: order_status"
    assert result["model"] == "gpt-6-luna"
    assert result["input_tokens"] == 20
    assert result["output_tokens"] == 8
    assert result["total_tokens"] == 28
    assert result["latency_ms"] >= 0

    fake_client.responses.create.assert_called_once()
