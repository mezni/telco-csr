from classifier import classify_ticket


def test_classifies_order_status():
    result = classify_ticket("My order #4821 has not arrived.")

    assert result == {
        "category": "order_status",
        "order_id": 4821,
        "needs_order_lookup": True,
    }


def test_extracts_order_id_without_hash():
    result = classify_ticket("My order 4821 is delayed.")

    assert result["order_id"] == 4821


def test_unknown_request_does_not_trigger_lookup():
    result = classify_ticket("I need help with my phone settings.")

    assert result["category"] == "unknown"
    assert result["needs_order_lookup"] is False
