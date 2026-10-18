
def score_prediction(
    expected: dict,
    predicted: dict,
) -> dict:
    """Compare a model prediction against the expected fields."""

    return {
        "category_correct": (
            expected["category"] == predicted.get("category")
        ),
        "order_id_correct": (
            expected["order_id"] == predicted.get("order_id")
        ),
        "lookup_correct": (
            expected["needs_order_lookup"]
            == predicted.get("needs_order_lookup")
        ),
    }


def summarize_scores(results: list[dict]) -> dict:
    """Calculate field-level accuracy across evaluation results."""

    if not results:
        return {
            "ticket_count": 0,
            "category_accuracy": 0.0,
            "order_id_accuracy": 0.0,
            "lookup_accuracy": 0.0,
            "overall_field_accuracy": 0.0,
        }

    count = len(results)

    category_accuracy = sum(
        r["category_correct"] for r in results
    ) / count

    order_id_accuracy = sum(
        r["order_id_correct"] for r in results
    ) / count

    lookup_accuracy = sum(
        r["lookup_correct"] for r in results
    ) / count

    total_correct = sum(
        r["category_correct"]
        + r["order_id_correct"]
        + r["lookup_correct"]
        for r in results
    )

    return {
        "ticket_count": count,
        "category_accuracy": category_accuracy,
        "order_id_accuracy": order_id_accuracy,
        "lookup_accuracy": lookup_accuracy,
        "overall_field_accuracy": total_correct / (count * 3),
    }

