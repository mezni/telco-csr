from experiment_dashboard import prepare_dashboard_data


def test_prepare_dashboard_data_converts_accuracy_to_percent():
    experiments = [
        {
            "id": 1,
            "model": "gpt-6-luna",
            "category_accuracy": 0.8,
            "order_id_accuracy": 0.6,
            "lookup_accuracy": 1.0,
            "overall_field_accuracy": 0.8,
            "average_latency_ms": 950.123,
            "total_input_tokens": 500,
            "total_output_tokens": 100,
        }
    ]

    rows = prepare_dashboard_data(experiments)

    assert len(rows) == 1
    assert rows[0]["Category accuracy (%)"] == 80.0
    assert rows[0]["Order ID accuracy (%)"] == 60.0
    assert rows[0]["Lookup accuracy (%)"] == 100.0
    assert rows[0]["Overall accuracy (%)"] == 80.0
    assert rows[0]["Average latency (ms)"] == 950.12


def test_prepare_dashboard_data_returns_oldest_first():
    base = {
        "model": "gpt-6-luna",
        "category_accuracy": 1.0,
        "order_id_accuracy": 1.0,
        "lookup_accuracy": 1.0,
        "overall_field_accuracy": 1.0,
        "average_latency_ms": 100,
        "total_input_tokens": 10,
        "total_output_tokens": 5,
    }

    experiments = [
        {**base, "id": 3},
        {**base, "id": 2},
        {**base, "id": 1},
    ]

    rows = prepare_dashboard_data(experiments)

    assert [row["Experiment"] for row in rows] == [
        "#1",
        "#2",
        "#3",
    ]


def test_prepare_dashboard_data_handles_empty_history():
    assert prepare_dashboard_data([]) == []
