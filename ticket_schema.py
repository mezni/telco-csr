from dataclasses import asdict, dataclass
from typing import Any

ALLOWED_CATEGORIES = {
    "order_status",
    "billing",
    "technical_support",
    "other",
}


@dataclass(frozen=True)
class TicketClassification:
    category: str
    order_id: int | None
    needs_order_lookup: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert the validated classification into a dictionary."""
        return asdict(self)


def validate_classification(data: Any) -> TicketClassification:
    """Validate untrusted classifier output and return a typed result."""
    if not isinstance(data, dict):
        raise ValueError("Classification must be a JSON object.")

    required_fields = {
        "category",
        "order_id",
        "needs_order_lookup",
    }

    missing_fields = required_fields - data.keys()
    extra_fields = data.keys() - required_fields

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {', '.join(sorted(missing_fields))}"
        )

    if extra_fields:
        raise ValueError(f"Unexpected fields: {', '.join(sorted(extra_fields))}")

    category = data["category"]
    order_id = data["order_id"]
    needs_order_lookup = data["needs_order_lookup"]

    if not isinstance(category, str) or category not in ALLOWED_CATEGORIES:
        raise ValueError(
            f"Invalid category. Allowed values: {sorted(ALLOWED_CATEGORIES)}"
        )

    # bool is a subclass of int in Python, so reject it explicitly.
    if order_id is not None:
        if isinstance(order_id, bool) or not isinstance(order_id, int):
            raise ValueError("order_id must be an integer or null.")

        if order_id <= 0:
            raise ValueError("order_id must be a positive integer.")

    if not isinstance(needs_order_lookup, bool):
        raise ValueError("needs_order_lookup must be a boolean.")

    return TicketClassification(
        category=category,
        order_id=order_id,
        needs_order_lookup=needs_order_lookup,
    )
