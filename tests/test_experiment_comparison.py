from experiment_comparison import compare_experiments


def make_experiment(
    experiment_id: int,
    accuracy: float,
    latency: float,
    input_tokens: int = 500,
    output_tokens: int = 100,
) -> dict:
    return {
        "id": experiment_id,
        "category_accuracy": accuracy,
        "order_id_accuracy": accuracy,
        "lookup_accuracy": accuracy,
        "overall_field_accuracy": accuracy,
        "average_latency_ms": latency,
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
    }


def test_detects_accuracy_improvement():
    baseline = make_experiment(1, accuracy=0.70, latency=800)
    candidate = make_experiment(2, accuracy=0.90, latency=850)

    result = compare_experiments(baseline, candidate)

    assert "overall_field_accuracy" in result["improvements"]
    assert "overall_field_accuracy" not in result["regressions"]


def test_detects_latency_regression():
    baseline = make_experiment(1, accuracy=0.80, latency=800)
    candidate = make_experiment(2, accuracy=0.80, latency=950)

    result = compare_experiments(baseline, candidate)

    assert "average_latency_ms" in result["regressions"]


def test_detects_token_reduction():
    baseline = make_experiment(
        1, accuracy=0.80, latency=800, input_tokens=500
    )
    candidate = make_experiment(
        2, accuracy=0.80, latency=800, input_tokens=350
    )

    result = compare_experiments(baseline, candidate)

    assert "total_input_tokens" in result["improvements"]


def test_identical_experiments_have_no_regressions():
    baseline = make_experiment(1, accuracy=0.80, latency=800)
    candidate = make_experiment(2, accuracy=0.80, latency=800)

    result = compare_experiments(baseline, candidate)

    assert result["improvements"] == []
    assert result["regressions"] == []
