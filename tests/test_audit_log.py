import audit_log


def test_log_event_persists_event(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audit_log,
        "DB_PATH",
        tmp_path / "audit.db",
    )

    event_id = audit_log.log_event(
        ticket_id="TICKET-001",
        event_type="classification_succeeded",
        details={"category": "order_status"},
    )

    events = audit_log.list_events(ticket_id="TICKET-001")

    assert event_id > 0
    assert len(events) == 1
    assert events[0]["ticket_id"] == "TICKET-001"
    assert events[0]["event_type"] == "classification_succeeded"
    assert events[0]["details"] == {"category": "order_status"}
    assert events[0]["timestamp"]


def test_list_events_filters_by_ticket(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audit_log,
        "DB_PATH",
        tmp_path / "audit.db",
    )

    audit_log.log_event("TICKET-001", "classification_succeeded")
    audit_log.log_event("TICKET-002", "classification_failed")

    events = audit_log.list_events(ticket_id="TICKET-002")

    assert len(events) == 1
    assert events[0]["ticket_id"] == "TICKET-002"


def test_list_events_respects_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audit_log,
        "DB_PATH",
        tmp_path / "audit.db",
    )

    for number in range(3):
        audit_log.log_event(
            "TICKET-001",
            "classification_succeeded",
            {"sequence": number},
        )

    events = audit_log.list_events(limit=2)

    assert len(events) == 2


def test_empty_ticket_id_is_rejected():
    import pytest

    with pytest.raises(ValueError, match="ticket_id"):
        audit_log.log_event("", "classification_succeeded")


def test_invalid_details_are_rejected():
    import pytest

    with pytest.raises(ValueError, match="details must be a dictionary"):
        audit_log.log_event(
            "TICKET-001",
            "classification_succeeded",
            ["not", "a", "dictionary"],
        )


def test_invalid_limit_is_rejected():
    import pytest

    with pytest.raises(ValueError, match="limit"):
        audit_log.list_events(limit=0)
