from reproducibility import (
    build_manifest,
    fingerprint_dataset,
    fingerprint_text,
)


def test_same_text_has_same_fingerprint():
    assert fingerprint_text("hello") == fingerprint_text("hello")


def test_changed_text_has_different_fingerprint():
    assert fingerprint_text("prompt A") != fingerprint_text("prompt B")


def test_dataset_fingerprint_ignores_key_order():
    dataset_a = [{"id": "T001", "ticket": "Example"}]
    dataset_b = [{"ticket": "Example", "id": "T001"}]

    assert fingerprint_dataset(dataset_a) == fingerprint_dataset(dataset_b)


def test_dataset_fingerprint_changes_when_content_changes():
    dataset_a = [{"id": "T001", "ticket": "Example"}]
    dataset_b = [{"id": "T001", "ticket": "Different example"}]

    assert fingerprint_dataset(dataset_a) != fingerprint_dataset(dataset_b)


def test_manifest_records_evaluation_inputs():
    manifest = build_manifest(
        prompt="Classify the ticket.",
        model="gpt-6-luna",
        dataset=[
            {
                "id": "T001",
                "ticket": "My order is delayed.",
                "expected": {
                    "category": "order_status",
                    "order_id": None,
                    "needs_order_lookup": True,
                },
            }
        ],
    )

    assert manifest["model"] == "gpt-6-luna"
    assert manifest["ticket_count"] == 1
    assert len(manifest["prompt_hash"]) == 64
    assert len(manifest["dataset_hash"]) == 64
    assert manifest["evaluator_version"] == "1.0.0"
