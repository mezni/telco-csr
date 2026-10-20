from unittest.mock import patch

from telco_csr.domain.intents import IntentClassification, TelecomIntent
from telco_csr.nodes.intent_router import intent_router_node


@patch("telco_csr.nodes.intent_router.get_llm")
def test_intent_router_billing_spike(mock_get_llm):
    # Mock the structured LLM return value
    mock_structured_llm = mock_get_llm.return_value.with_structured_output.return_value
    mock_structured_llm.invoke.return_value = IntentClassification(
        intent=TelecomIntent.BILLING_SPIKE,
        confidence=0.95,
        reasoning="User is complaining about an unexpectedly high bill.",
    )

    state = {"latest_user_message": "Why is my bill $200 higher this month?"}
    result = intent_router_node(state)

    assert result["current_intent"] == "BILLING_SPIKE"
    assert result["router_confidence"] == 0.95


@patch("telco_csr.nodes.intent_router.get_llm")
def test_intent_router_low_confidence_fallback(mock_get_llm):
    # Mock a low confidence score below the 0.70 threshold
    mock_structured_llm = mock_get_llm.return_value.with_structured_output.return_value
    mock_structured_llm.invoke.return_value = IntentClassification(
        intent=TelecomIntent.CREDIT_REQUEST,
        confidence=0.45,
        reasoning="Ambiguous statement.",
    )

    state = {"latest_user_message": "Hmm not sure."}
    result = intent_router_node(state)

    # Should fall back to GENERAL_FAQ due to confidence < 0.70
    assert result["current_intent"] == "GENERAL_FAQ"
    assert result["router_confidence"] == 0.45
