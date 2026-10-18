from error_analysis import analyze_errors


def make_detail(
    ticket_id,
    category,
    category_correct=True,
    order_id_correct=True,
    lookup_correct=True,
):
    return {
        "id": ticket_id,
        "ticket": "Example customer ticket",
        "expected": {
            "category": category,
            "order_id": 4821,
            "needs_order_lookup": True,
        },
        "predicted": {
            "category": category if category_correct else "other",
            "order_id": 4821 if order_id_correct else 9999,
            "needs_order_lookup": lookup_correct,
        },
        "scores": {
            "category_correct": category_correct,
            "order_id_correct": order_id_correct,
            "lookup_correct": lookup_correct,
        },
        "parse_error": None,
    }


def test_summarizes_metrics_by_expected_category():
    details = [
        make_detail("T001", "billing"),
        make_detail("T002", "billing", category_correct=False),
        make_detail("T003", "order_status"),
    ]

    result = analyze_errors(details)
    billing = result["category_summary"]["billing"]

    assert billing["ticket_count"] == 2
    assert billing["category_correct"] == 1
    assert billing["category_accuracy"] == 0.5
    assert billing["error_count"] == 1


def test_detects_field_level_errors():
    details = [
        make_detail("T001", "billing", order_id_correct=False),
    ]

    result = analyze_errors(details)

    assert result["error_count"] == 1
    assert result["errors"][0]["order_id_correct"] is False
    assert result["errors"][0]["category_correct"] is True


def test_counts_fully_correct_tickets():
    result = analyze_errors([
        make_detail("T001", "billing"),
        make_detail("T002", "billing", lookup_correct=False),
    ])

    billing = result["category_summary"]["billing"]

    assert billing["fully_correct"] == 1
    assert billing["overall_field_accuracy"] == 5 / 6


def test_handles_empty_results():
    result = analyze_errors([])

    assert result["ticket_count"] == 0
    assert result["error_count"] == 0
    assert result["category_summary"] == {}
    assert result["errors"] == []
