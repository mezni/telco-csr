from langchain_core.messages import HumanMessage, SystemMessage

from telco_csr.core.llm_factory import get_llm
from telco_csr.core.logger import log_intent_metrics
from telco_csr.domain.intents import IntentClassification, TelecomIntent

ROUTER_SYSTEM_PROMPT = """You are an expert intent classification engine \
for a Telecommunications Billing Assistant.
Analyze the customer's incoming message and classify it \
into exactly ONE operational intent:

- BILLING_SPIKE: Inquiries about unexpectedly high bills,
  sudden data/roaming overages, or unexplained charges.
- CREDIT_REQUEST: Requests for fee waivers, bill credits,
  refunds, or adjustments for service outages.
- PAYMENT_EXTENSION: Requests for extra time to pay past-due bills,
  payment arrangements, or promise-to-pay dates.
- PLAN_CHANGE: Questions or requests about upgrading, downgrading,
  or changing current rate plans and add-on packs.
- GENERAL_FAQ: General queries about billing cycles, accepted payment methods,
  store locations, or standard support policies.
- UNKNOWN: Completely off-topic or ambiguous queries that do not fit
  any operational telecom category.
"""


@log_intent_metrics
def intent_router_node(state: dict) -> dict:
    """
    Classifies the latest user message and updates the graph state with the intent.
    """
    user_message = state.get("latest_user_message", "")

    # Instantiate LLM with structured output binding
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(IntentClassification)

    messages = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    try:
        result: IntentClassification = structured_llm.invoke(messages)
    except Exception:
        # Fallback safeguard if LLM call fails
        result = IntentClassification(
            intent=TelecomIntent.GENERAL_FAQ,
            confidence=0.0,
            reasoning="Fallback triggered due to classification invocation error.",
        )

    # Apply confidence threshold fallback (< 0.70 defaults to GENERAL_FAQ)
    final_intent = (
        result.intent if result.confidence >= 0.70 else TelecomIntent.GENERAL_FAQ
    )

    return {
        "current_intent": final_intent.value,
        "router_confidence": result.confidence,
        "router_reasoning": result.reasoning,
    }
