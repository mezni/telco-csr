from dataset_validation import validate_dataset


def valid_ticket(ticket_id="T001"):
    return {
        "id": ticket_id,
        "ticket": "My order #4821 has not arrived.",
        "expected": {
            "category": "order_status",
            "order_id": 4821,
            "needs_order_lookup": True,
        },
        "scenario": "order_status",
    }


def test_valid_dataset_has_no_errors():
    assert validate_dataset([valid_ticket()]) == []


def test_duplicate_ids_are_rejected():
    errors = validate_dataset([
        valid_ticket("T001"),
        valid_ticket("T001"),
    ])

    assert any("duplicate id" in error for error in errors)


def test_invalid_category_is_rejected():
    item = valid_ticket()
    item["expected"]["category"] = "unknown"

    errors = validate_dataset([item])

    assert any("invalid category" in error for error in errors)


def test_invalid_order_id_is_rejected():
    item = valid_ticket()
    item["expected"]["order_id"] = -42

    errors = validate_dataset([item])

    assert any("order_id" in error for error in errors)


def test_boolean_is_not_accepted_as_order_id():
    item = valid_ticket()
    item["expected"]["order_id"] = True

    errors = validate_dataset([item])

    assert any("order_id" in error for error in errors)


def test_empty_ticket_is_rejected():
    item = valid_ticket()
    item["ticket"] = "   "

    errors = validate_dataset([item])

    assert any("ticket must be non-empty text" in error for error in errors)


def test_invalid_lookup_flag_is_rejected():
    item = valid_ticket()
    item["expected"]["needs_order_lookup"] = "yes"

    errors = validate_dataset([item])

    assert any("needs_order_lookup" in error for error in errors)
