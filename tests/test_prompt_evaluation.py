from unittest.mock import patch

from prompt_evaluation import run_prompt_evaluation


def test_prompt_evaluation_scores_mocked_responses():
    tickets = [
        {
            "id": "T001",
            "ticket": "My order #4821 has not arrived.",
            "expected": {
                "category": "order_status",
                "order_id": 4821,
                "needs_order_lookup": True,
            },
        }
    ]

    mocked_run = {
        "model": "test-model",
        "response": (
            '{"category": "order_status", "order_id": 4821, "needs_order_lookup": true}'
        ),
        "latency_ms": 120.0,
        "input_tokens": 20,
        "output_tokens": 12,
        "total_tokens": 32,
    }

    with patch(
        "prompt_evaluation.run_inference",
        return_value=mocked_run,
    ) as mock_inference:
        result = run_prompt_evaluation(
            prompt="Test prompt",
            model="test-model",
            tickets=tickets,
        )

    assert result["ticket_count"] == 1
    assert result["summary"]["category_accuracy"] == 1.0
    assert result["summary"]["order_id_accuracy"] == 1.0
    assert result["summary"]["lookup_accuracy"] == 1.0
    assert result["average_latency_ms"] == 120.0
    assert result["total_input_tokens"] == 20
    assert result["total_output_tokens"] == 12
    mock_inference.assert_called_once()
