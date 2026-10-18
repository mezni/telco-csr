import audit_log
from metrics import build_metrics_report


def test_metrics_report_calculates_outcomes(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audit_log,
        "DB_PATH",
        tmp_path / "audit.db",
    )

    audit_log.log_event(
        ticket_id="T-001",
        event_type="classification_succeeded",
        details={"attempt_count": 1, "latency_ms": 200},
    )
    audit_log.log_event(
        ticket_id="T-002",
        event_type="classification_succeeded",
        details={"attempt_count": 2, "latency_ms": 400},
    )
    audit_log.log_event(
        ticket_id="T-003",
        event_type="classification_failed",
        details={"attempt_count": 3},
    )

    report = build_metrics_report()

    assert report["tickets_processed"] == 3
    assert report["success_count"] == 2
    assert report["failure_count"] == 1
    assert report["success_rate"] == 0.6667
    assert report["manual_review_rate"] == 0.3333
    assert report["average_latency_ms"] == 300
    assert report["average_attempt_count"] == 2
    assert report["latency_sample_count"] == 2


def test_metrics_report_handles_empty_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audit_log,
        "DB_PATH",
        tmp_path / "empty-audit.db",
    )

    report = build_metrics_report()

    assert report["tickets_processed"] == 0
    assert report["success_rate"] == 0.0
    assert report["manual_review_rate"] == 0.0
    assert report["average_latency_ms"] is None
    assert report["average_attempt_count"] is None
