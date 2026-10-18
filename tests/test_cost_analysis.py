
import pytest

from cost_analysis import (
    analyze_experiment,
    analyze_performance,
    estimate_cost,
    percentile,
)


def test_estimate_cost():
    result = estimate_cost(
        input_tokens=100_000,
        output_tokens=20_000,
        input_price_per_million=1.0,
        output_price_per_million=4.0,
    )

    assert result["input_cost_usd"] == pytest.approx(0.10)
    assert result["output_cost_usd"] == pytest.approx(0.08)
    assert result["total_cost_usd"] == pytest.approx(0.18)


def test_zero_tokens_have_zero_cost():
    result = estimate_cost(0, 0, 1.0, 4.0)

    assert result["total_cost_usd"] == 0.0


@pytest.mark.parametrize(
    "tokens,input_price,output_price",
    [
        (-1, 1.0, 1.0),
        (100, -1.0, 1.0),
        (100, 1.0, -1.0),
    ],
)
def test_negative_cost_inputs_are_rejected(
    tokens,
    input_price,
    output_price,
):
    with pytest.raises(ValueError):
        estimate_cost(tokens, 10, input_price, output_price)


def test_percentile():
    assert percentile([10, 20, 30, 40, 50], 95) == 50
    assert percentile([], 95) == 0.0


def test_performance_metrics():
    result = analyze_performance([100, 200, 300, 400, 500])

    assert result["average_latency_ms"] == pytest.approx(300)
    assert result["median_latency_ms"] == 300
    assert result["p95_latency_ms"] == 500


def test_analyze_experiment():
    experiment = {
        "ticket_count": 2,
        "total_input_tokens": 100_000,
        "total_output_tokens": 20_000,
        "details": [
            {"latency_ms": 100},
            {"latency_ms": 300},
        ],
    }

    result = analyze_experiment(
        experiment,
        input_price_per_million=1.0,
        output_price_per_million=4.0,
    )

    assert result["total_cost_usd"] == pytest.approx(0.18)
    assert result["cost_per_ticket_usd"] == pytest.approx(0.09)
    assert result["total_tokens"] == 120_000
    assert result["median_latency_ms"] == 200

