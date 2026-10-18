import re


def classify_ticket(message: str) -> dict:
    """Classify a telecom support ticket using simple rules."""
    text = message.lower()

    order_match = re.search(r"\border\s*#?\s*(\d+)\b", text)

    if "order" in text and any(
        phrase in text
        for phrase in ("not arrived", "where is", "delivery", "tracking", "delayed")
    ):
        return {
            "category": "order_status",
            "order_id": int(order_match.group(1)) if order_match else None,
            "needs_order_lookup": True,
        }

    return {
        "category": "unknown",
        "order_id": None,
        "needs_order_lookup": False,
    }
