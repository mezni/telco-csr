from evaluation_gates import evaluate_gates


def make_experiment(
    overall_accuracy=0.90,
    category_accuracy=0.95,
    latency_ms=1200.0,
    details=None,
):
    return {
        "overall_field_accuracy": overall_accuracy,
        "category_accuracy": category_accuracy,
        "average_latency_ms": latency_ms,
        "details": details or [],
    }


def test_approves_experiment_that_passes_all_gates():
    result = evaluate_gates(make_experiment())

    assert result["approved"] is True
    assert result["failures"] == []


def test_rejects_experiment_with_low_accuracy():
    result = evaluate_gates(
        make_experiment(overall_accuracy=0.70)
    )

    assert result["approved"] is False
    assert "overall_accuracy" in result["failures"]


def test_rejects_experiment_with_high_latency():
    result = evaluate_gates(
        make_experiment(latency_ms=2500.0)
    )

    assert result["approved"] is False
    assert "latency" in result["failures"]


def test_rejects_invalid_json():
    result = evaluate_gates(
        make_experiment(
            details=[
                {"parse_error": "Invalid JSON response"},
            ]
        )
    )

    assert result["approved"] is False
    assert "invalid_json" in result["failures"]


def test_accepts_values_exactly_at_thresholds():
    result = evaluate_gates(
        make_experiment(
            overall_accuracy=0.85,
            category_accuracy=0.90,
            latency_ms=2000.0,
        )
    )

    assert result["approved"] is True
