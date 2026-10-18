from collections import defaultdict


def analyze_errors(details: list[dict]) -> dict:
    """Summarize evaluation performance by expected category."""

    categories = defaultdict(
        lambda: {
            "ticket_count": 0,
            "category_correct": 0,
            "order_id_correct": 0,
            "lookup_correct": 0,
            "fully_correct": 0,
            "error_count": 0,
        }
    )

    errors = []

    for item in details:
        expected = item.get("expected", {})
        predicted = item.get("predicted", {})
        scores = item.get("scores", {})

        category = expected.get("category", "unknown")
        stats = categories[category]

        category_correct = bool(scores.get("category_correct", False))
        order_id_correct = bool(scores.get("order_id_correct", False))
        lookup_correct = bool(scores.get("lookup_correct", False))

        fully_correct = category_correct and order_id_correct and lookup_correct

        stats["ticket_count"] += 1
        stats["category_correct"] += int(category_correct)
        stats["order_id_correct"] += int(order_id_correct)
        stats["lookup_correct"] += int(lookup_correct)
        stats["fully_correct"] += int(fully_correct)
        stats["error_count"] += int(not fully_correct)

        if not fully_correct:
            errors.append(
                {
                    "id": item.get("id", "unknown"),
                    "ticket": item.get("ticket", ""),
                    "expected_category": category,
                    "predicted_category": predicted.get("category", "missing"),
                    "expected_order_id": expected.get("order_id"),
                    "predicted_order_id": predicted.get("order_id"),
                    "expected_lookup": expected.get("needs_order_lookup"),
                    "predicted_lookup": predicted.get("needs_order_lookup"),
                    "category_correct": category_correct,
                    "order_id_correct": order_id_correct,
                    "lookup_correct": lookup_correct,
                    "parse_error": item.get("parse_error"),
                }
            )

    summary = {}

    for category, stats in categories.items():
        count = stats["ticket_count"]

        summary[category] = {
            **stats,
            "category_accuracy": stats["category_correct"] / count,
            "order_id_accuracy": stats["order_id_correct"] / count,
            "lookup_accuracy": stats["lookup_correct"] / count,
            "overall_field_accuracy": (
                stats["category_correct"]
                + stats["order_id_correct"]
                + stats["lookup_correct"]
            )
            / (count * 3),
        }

    return {
        "category_summary": summary,
        "errors": errors,
        "ticket_count": len(details),
        "error_count": len(errors),
    }
