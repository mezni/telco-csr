def evaluate_gates(
    experiment: dict,
    min_overall_accuracy: float = 0.85,
    min_category_accuracy: float = 0.90,
    max_latency_ms: float = 2000.0,
    max_invalid_json: int = 0,
) -> dict:
    """Check whether an experiment satisfies evaluation requirements."""

    invalid_json_count = sum(
        1
        for detail in experiment.get("details", [])
        if detail.get("parse_error")
    )

    checks = {
        "overall_accuracy": {
            "actual": experiment["overall_field_accuracy"],
            "threshold": min_overall_accuracy,
            "passed": (
                experiment["overall_field_accuracy"]
                >= min_overall_accuracy
            ),
        },
        "category_accuracy": {
            "actual": experiment["category_accuracy"],
            "threshold": min_category_accuracy,
            "passed": (
                experiment["category_accuracy"]
                >= min_category_accuracy
            ),
        },
        "latency": {
            "actual": experiment["average_latency_ms"],
            "threshold": max_latency_ms,
            "passed": experiment["average_latency_ms"] <= max_latency_ms,
        },
        "invalid_json": {
            "actual": invalid_json_count,
            "threshold": max_invalid_json,
            "passed": invalid_json_count <= max_invalid_json,
        },
    }

    failures = [
        name for name, check in checks.items()
        if not check["passed"]
    ]

    return {
        "approved": not failures,
        "checks": checks,
        "failures": failures,
    }
