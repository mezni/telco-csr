from evaluator import score_prediction, summarize_scores


def test_all_fields_correct():
    expected = {
        "category": "order_status",
        "order_id": 4821,
        "needs_order_lookup": True,
    }

    result = score_prediction(expected, expected)

    assert result == {
        "category_correct": True,
        "order_id_correct": True,
        "lookup_correct": True,
    }


def test_wrong_order_id_is_detected():
    expected = {
        "category": "order_status",
        "order_id": 4821,
        "needs_order_lookup": True,
    }

    predicted = {
        "category": "order_status",
        "order_id": 9999,
        "needs_order_lookup": True,
    }

    result = score_prediction(expected, predicted)

    assert result["category_correct"] is True
    assert result["order_id_correct"] is False
    assert result["lookup_correct"] is True


def test_summary_calculates_accuracy():
    results = [
        {
            "category_correct": True,
            "order_id_correct": True,
            "lookup_correct": True,
        },
        {
            "category_correct": True,
            "order_id_correct": False,
            "lookup_correct": True,
        },
    ]

    summary = summarize_scores(results)

    assert summary["ticket_count"] == 2
    assert summary["category_accuracy"] == 1.0
    assert summary["order_id_accuracy"] == 0.5
    assert summary["lookup_accuracy"] == 1.0
    assert summary["overall_field_accuracy"] == 5 / 6


def test_empty_results():
    summary = summarize_scores([])

    assert summary["ticket_count"] == 0
    assert summary["overall_field_accuracy"] == 0.0
