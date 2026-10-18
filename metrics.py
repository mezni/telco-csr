# metrics.py

from statistics import mean
from typing import Any

from audit_log import list_events


def build_metrics_report(limit: int = 10_000) -> dict[str, Any]:
    """Calculate metrics from the most recent audit events."""
    events = list_events(limit=limit)

    successes = [
        event for event in events if event["event_type"] == "classification_succeeded"
    ]
    failures = [
        event for event in events if event["event_type"] == "classification_failed"
    ]

    processed = successes + failures
    total = len(processed)

    latencies = [
        event["details"]["latency_ms"]
        for event in successes
        if isinstance(event["details"].get("latency_ms"), (int, float))
        and not isinstance(event["details"].get("latency_ms"), bool)
    ]

    attempts = [
        event["details"]["attempt_count"]
        for event in processed
        if isinstance(event["details"].get("attempt_count"), int)
        and not isinstance(event["details"].get("attempt_count"), bool)
    ]

    success_rate = len(successes) / total if total else 0.0
    manual_review_rate = len(failures) / total if total else 0.0

    return {
        "tickets_processed": total,
        "success_count": len(successes),
        "failure_count": len(failures),
        "success_rate": round(success_rate, 4),
        "manual_review_rate": round(manual_review_rate, 4),
        "average_latency_ms": (round(mean(latencies), 2) if latencies else None),
        "average_attempt_count": (round(mean(attempts), 2) if attempts else None),
        "latency_sample_count": len(latencies),
        "attempt_sample_count": len(attempts),
        "events_scanned": len(events),
    }
