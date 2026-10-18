def compare_experiments(
    baseline: dict,
    candidate: dict,
) -> dict:
    """Compare two saved experiments and identify metric regressions."""

    metrics = {
        "category_accuracy": "higher",
        "order_id_accuracy": "higher",
        "lookup_accuracy": "higher",
        "overall_field_accuracy": "higher",
        "average_latency_ms": "lower",
        "total_input_tokens": "lower",
        "total_output_tokens": "lower",
    }

    comparisons = {}

    for metric, direction in metrics.items():
        baseline_value = baseline[metric]
        candidate_value = candidate[metric]

        if direction == "higher":
            improved = candidate_value > baseline_value
            regressed = candidate_value < baseline_value
        else:
            improved = candidate_value < baseline_value
            regressed = candidate_value > baseline_value

        comparisons[metric] = {
            "baseline": baseline_value,
            "candidate": candidate_value,
            "difference": candidate_value - baseline_value,
            "improved": improved,
            "regressed": regressed,
        }

    regressions = [
        metric for metric, result in comparisons.items() if result["regressed"]
    ]

    improvements = [
        metric for metric, result in comparisons.items() if result["improved"]
    ]

    return {
        "baseline_id": baseline["id"],
        "candidate_id": candidate["id"],
        "comparisons": comparisons,
        "improvements": improvements,
        "regressions": regressions,
    }
