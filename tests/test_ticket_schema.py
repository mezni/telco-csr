import pytest

from ticket_schema import (
    TicketClassification,
    validate_classification,
)


def test_valid_order_status_classification():
    result = validate_classification(
        {
            "category": "order_status",
            "order_id": 4821,
            "needs_order_lookup": True,
        }
    )

    assert result == TicketClassification(
        category="order_status",
        order_id=4821,
        needs_order_lookup=True,
    )


def test_order_id_can_be_null():
    result = validate_classification(
        {
            "category": "billing",
            "order_id": None,
            "needs_order_lookup": False,
        }
    )

    assert result.order_id is None


def test_to_dict_returns_structured_data():
    result = validate_classification(
        {
            "category": "other",
            "order_id": None,
            "needs_order_lookup": False,
        }
    )

    assert result.to_dict() == {
        "category": "other",
        "order_id": None,
        "needs_order_lookup": False,
    }


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        "not an object",
    ],
)
def test_rejects_non_object(data):
    with pytest.raises(ValueError):
        validate_classification(data)


def test_rejects_missing_fields():
    with pytest.raises(ValueError, match="Missing required fields"):
        validate_classification(
            {
                "category": "billing",
                "order_id": None,
            }
        )


def test_rejects_extra_fields():
    with pytest.raises(ValueError, match="Unexpected fields"):
        validate_classification(
            {
                "category": "billing",
                "order_id": None,
                "needs_order_lookup": False,
                "customer_email": "example@example.com",
            }
        )


def test_rejects_unknown_category():
    with pytest.raises(ValueError, match="Invalid category"):
        validate_classification(
            {
                "category": "refund",
                "order_id": None,
                "needs_order_lookup": False,
            }
        )


@pytest.mark.parametrize("order_id", ["4821", True, 0, -5, 3.14])
def test_rejects_invalid_order_id(order_id):
    with pytest.raises(ValueError):
        validate_classification(
            {
                "category": "order_status",
                "order_id": order_id,
                "needs_order_lookup": True,
            }
        )


def test_rejects_non_boolean_lookup_flag():
    with pytest.raises(ValueError, match="must be a boolean"):
        validate_classification(
            {
                "category": "order_status",
                "order_id": 4821,
                "needs_order_lookup": "true",
            }
        )
