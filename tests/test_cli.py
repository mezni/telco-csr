from unittest.mock import patch

from cli import main


@patch("cli.decide_approval")
@patch("cli.process_ticket")
def test_triage_approves_recommendation(
    mock_process,
    mock_decide,
):
    recommendation = {
        "status": "pending_approval",
        "ticket_id": "TICKET-001",
        "classification": {
            "category": "order_status",
            "order_id": 4821,
            "needs_order_lookup": True,
        },
    }
    mock_process.return_value = recommendation
    mock_decide.return_value = {
        **recommendation,
        "status": "approved",
        "decision": "approve",
        "reviewer": "reviewer-1",
    }

    with (
        patch("builtins.input", side_effect=["y", "reviewer-1"]),
    ):
        result = main([
            "triage",
            "--ticket", "My order #4821 has not arrived.",
            "--model", "test-model",
            "--ticket-id", "TICKET-001",
        ])

    assert result == 0
    mock_decide.assert_called_once_with(
        recommendation,
        decision="approve",
        reviewer="reviewer-1",
    )


@patch("cli.process_ticket")
def test_failed_classification_does_not_request_approval(
    mock_process,
):
    mock_process.return_value = {
        "status": "needs_review",
        "ticket_id": "TICKET-001",
        "classification": None,
        "error": "Invalid model output",
    }

    with patch("builtins.input") as mock_input:
        result = main([
            "triage",
            "--ticket", "My order is late.",
            "--model", "test-model",
        ])

    assert result == 1
    mock_input.assert_not_called()


@patch("cli.list_events")
def test_history_displays_events(mock_list_events):
    mock_list_events.return_value = [
        {
            "id": 1,
            "ticket_id": "TICKET-001",
            "event_type": "classification_succeeded",
            "details": {"category": "order_status"},
        }
    ]

    result = main([
        "history",
        "--ticket-id", "TICKET-001",
        "--limit", "10",
    ])

    assert result == 0
    mock_list_events.assert_called_once_with(
        ticket_id="TICKET-001",
        limit=10,
    )
