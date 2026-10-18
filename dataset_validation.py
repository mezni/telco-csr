ALLOWED_CATEGORIES = {
    "order_status",
    "billing",
    "technical_support",
    "other",
}


def validate_dataset(dataset: list[dict]) -> list[str]:
    """Return validation errors. An empty list means the dataset is valid."""
    errors = []
    seen_ids = set()

    for index, item in enumerate(dataset):
        location = f"Ticket at index {index}"

        if not isinstance(item, dict):
            errors.append(f"{location} must be an object.")
            continue

        ticket_id = item.get("id")
        ticket = item.get("ticket")
        expected = item.get("expected")

        if not isinstance(ticket_id, str) or not ticket_id.strip():
            errors.append(f"{location}: missing or invalid id.")
        elif ticket_id in seen_ids:
            errors.append(f"{location}: duplicate id '{ticket_id}'.")
        else:
            seen_ids.add(ticket_id)

        if not isinstance(ticket, str) or not ticket.strip():
            errors.append(f"{location}: ticket must be non-empty text.")

        if not isinstance(expected, dict):
            errors.append(f"{location}: expected must be an object.")
            continue

        category = expected.get("category")
        order_id = expected.get("order_id")
        needs_lookup = expected.get("needs_order_lookup")

        if category not in ALLOWED_CATEGORIES:
            errors.append(f"{location}: invalid category '{category}'.")

        if order_id is not None and (
            isinstance(order_id, bool) or not isinstance(order_id, int) or order_id <= 0
        ):
            errors.append(f"{location}: order_id must be a positive integer or null.")

        if not isinstance(needs_lookup, bool):
            errors.append(f"{location}: needs_order_lookup must be true or false.")

    return errors
