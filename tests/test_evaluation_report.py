
from evaluation_report import build_evaluation_report


def test_report_includes_metrics_and_manifest():
    experiment = {
        "id": 12,
        "created_at": "2026-10-18T12:00:00+00:00",
        "model": "example-model",
        "prompt": "Classify the ticket.",
        "prompt_name": "Baseline",
        "prompt_version": "v1",
        "ticket_count": 1,
        "category_accuracy": 1.0,
        "order_id_accuracy": 1.0,
        "lookup_accuracy": 1.0,
        "overall_field_accuracy": 1.0,
        "average_latency_ms": 100.0,
        "total_input_tokens": 100,
        "total_output_tokens": 20,
        "details": [
            {
                "id": "T001",
                "ticket": "Where is order #4821?",
                "expected": {
                    "category": "order_status",
                    "order_id": 4821,
                    "needs_order_lookup": True,
                },
                "predicted": {
                    "category": "order_status",
                    "order_id": 4821,
                    "needs_order_lookup": True,
                },
                "scores": {
                    "category_correct": True,
                    "order_id_correct": True,
                    "lookup_correct": True,
                },
                "latency_ms": 100.0,
                "total_tokens": 120,
                "parse_error": None,
            }
        ],
        "manifest": {
            "manifest_version": "1.0",
            "prompt_hash": "abc123",
            "dataset_hash": "def456",
            "evaluator_version": "1.0.0",
            "model": "example-model",
            "ticket_count": 1,
        },
        "prompt_hash": "abc123",
    }

    report = build_evaluation_report(
        experiment=experiment,
        input_price_per_million=1.0,
        output_price_per_million=4.0,
    )

    assert "# Ticket-Triage Evaluation Report" in report
    assert "Category accuracy" in report
    assert "Estimated total cost" in report
    assert "Evaluation Gates" in report
    assert "abc123" in report
    assert "All configured evaluation gates passed." in report


def test_report_flags_invalid_json():
    experiment = {
        "id": 13,
        "model": "example-model",
        "prompt_name": "Invalid output test",
        "prompt_version": "v1",
        "ticket_count": 1,
        "category_accuracy": 0.0,
        "order_id_accuracy": 0.0,
        "lookup_accuracy": 0.0,
        "overall_field_accuracy": 0.0,
        "average_latency_ms": 100.0,
        "total_input_tokens": 10,
        "total_output_tokens": 10,
        "details": [
            {
                "id": "T002",
                "ticket": "My bill is incorrect.",
                "expected": {
                    "category": "billing",
                    "order_id": None,
                    "needs_order_lookup": False,
                },
                "predicted": {},
                "scores": {
                    "category_correct": False,
                    "order_id_correct": False,
                    "lookup_correct": False,
                },
                "latency_ms": 100.0,
                "total_tokens": 20,
                "parse_error": "Invalid JSON response",
            }
        ],
        "manifest": {},
    }

    report = build_evaluation_report(
        experiment=experiment,
        input_price_per_million=1.0,
        output_price_per_million=4.0,
    )

    assert "**Gate status: FAIL**" in report
    assert "invalid_json" in report
    assert "Invalid JSON response" in report

