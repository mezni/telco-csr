
import experiment_store


def test_save_and_retrieve_experiment(tmp_path, monkeypatch):
    db_path = tmp_path / "experiments.db"
    monkeypatch.setattr(experiment_store, "DB_PATH", db_path)

    experiment_store.initialize_database()

    result = {
        "model": "test-model",
        "ticket_count": 1,
        "summary": {
            "category_accuracy": 1.0,
            "order_id_accuracy": 1.0,
            "lookup_accuracy": 1.0,
            "overall_field_accuracy": 1.0,
        },
        "average_latency_ms": 120.0,
        "total_input_tokens": 20,
        "total_output_tokens": 12,
        "details": [
            {
                "id": "T001",
                "ticket": "My order #4821 has not arrived.",
                "expected": {
                    "category": "order_status",
                    "order_id": 4821,
                    "needs_order_lookup": True,
                },
                "predicted": {
                    "category": "order_status",
                    "order_id": 4821,
                    "needs_order_lookup": True,
                },
                "scores": {
                    "category_correct": True,
                    "order_id_correct": True,
                    "lookup_correct": True,
                },
                "latency_ms": 120.0,
                "total_tokens": 32,
                "parse_error": None,
            }
        ],
    }

    experiment_id = experiment_store.save_experiment(
        "Test prompt",
        result,
    )

    saved = experiment_store.get_experiment(experiment_id)

    assert saved is not None
    assert saved["model"] == "test-model"
    assert saved["prompt"] == "Test prompt"
    assert saved["category_accuracy"] == 1.0
    assert saved["details"][0]["id"] == "T001"

    history = experiment_store.list_experiments()
    assert len(history) == 1
    assert history[0]["id"] == experiment_id

