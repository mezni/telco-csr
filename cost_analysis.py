def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    input_price_per_million: float,
    output_price_per_million: float,
) -> dict:
    """Estimate API cost in USD using configurable token prices."""
    values = (
        input_tokens,
        output_tokens,
        input_price_per_million,
        output_price_per_million,
    )

    if any(value < 0 for value in values):
        raise ValueError("Token counts and prices must be non-negative.")

    input_cost = input_tokens / 1_000_000 * input_price_per_million
    output_cost = output_tokens / 1_000_000 * output_price_per_million

    return {
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": input_cost + output_cost,
    }


def percentile(values: list[float], percentile_value: float) -> float:
    """Return a nearest-rank percentile from a non-empty list."""
    if not values:
        return 0.0

    if not 0 <= percentile_value <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    ordered = sorted(values)
    rank = max(
        1,
        int((percentile_value / 100) * len(ordered) + 0.999999),
    )
    return ordered[min(rank - 1, len(ordered) - 1)]


def analyze_performance(
    latencies_ms: list[float],
) -> dict:
    """Summarize average, median, and p95 latency in milliseconds."""
    if not latencies_ms:
        return {
            "average_latency_ms": 0.0,
            "median_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
        }

    if any(value < 0 for value in latencies_ms):
        raise ValueError("Latencies must be non-negative.")

    ordered = sorted(latencies_ms)
    middle = len(ordered) // 2

    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / 2

    return {
        "average_latency_ms": sum(ordered) / len(ordered),
        "median_latency_ms": median,
        "p95_latency_ms": percentile(ordered, 95),
    }


def analyze_experiment(
    experiment: dict,
    input_price_per_million: float,
    output_price_per_million: float,
) -> dict:
    """Combine saved token usage, cost estimates, and latency metrics."""
    cost = estimate_cost(
        input_tokens=experiment.get("total_input_tokens", 0),
        output_tokens=experiment.get("total_output_tokens", 0),
        input_price_per_million=input_price_per_million,
        output_price_per_million=output_price_per_million,
    )

    details = experiment.get("details", [])
    latencies = [
        float(item["latency_ms"])
        for item in details
        if item.get("latency_ms") is not None
    ]

    ticket_count = experiment.get("ticket_count", 0)

    return {
        **cost,
        **analyze_performance(latencies),
        "ticket_count": ticket_count,
        "cost_per_ticket_usd": (
            cost["total_cost_usd"] / ticket_count if ticket_count > 0 else 0.0
        ),
        "total_tokens": (
            experiment.get("total_input_tokens", 0)
            + experiment.get("total_output_tokens", 0)
        ),
    }
