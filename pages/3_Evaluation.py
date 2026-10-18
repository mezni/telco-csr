
import json
from pathlib import Path

import streamlit as st

from evaluator import score_prediction, summarize_scores
from llm_service import DEFAULT_MODEL, run_inference

st.set_page_config(page_title="LLM Evaluation", layout="wide")
st.title("LLM Evaluation Lab")

DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "eval_tickets.json"

SYSTEM_PROMPT = """
You classify telecom support tickets.

Return one JSON object with exactly these fields:
- category: order_status, billing, technical_support, or other
- order_id: integer if present, otherwise null
- needs_order_lookup: boolean

Rules:
- An order-status ticket with an order ID requires an order lookup.
- Billing and technical-support tickets do not require an order lookup.
- Do not invent an order ID.
- Return JSON only, without Markdown fences or extra commentary.
"""

model = st.text_input("Model", value=DEFAULT_MODEL)

if st.button("Run evaluation", type="primary"):
    tickets = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    results = []
    details = []
    progress = st.progress(0)
    status = st.empty()

    try:
        for index, item in enumerate(tickets):
            status.write(f'Evaluating {item["id"]}: {item["ticket"]}')

            run = run_inference(
                ticket=item["ticket"],
                system_prompt=SYSTEM_PROMPT,
                model=model.strip(),
            )

            try:
                predicted = json.loads(run["response"])
                scores = score_prediction(item["expected"], predicted)
                parse_error = None
            except (json.JSONDecodeError, TypeError):
                predicted = {}
                scores = {
                    "category_correct": False,
                    "order_id_correct": False,
                    "lookup_correct": False,
                }
                parse_error = "Model response was not valid JSON."

            results.append(scores)
            details.append({
                "id": item["id"],
                "ticket": item["ticket"],
                "expected": item["expected"],
                "predicted": predicted,
                "scores": scores,
                "latency_ms": run["latency_ms"],
                "total_tokens": run["total_tokens"],
                "parse_error": parse_error,
            })

            progress.progress((index + 1) / len(tickets))

        st.session_state["evaluation_summary"] = summarize_scores(results)
        st.session_state["evaluation_details"] = details
        st.session_state["evaluation_model"] = model.strip()
        status.success("Evaluation completed.")

    except Exception as exc:
        status.error(f"Evaluation failed: {exc}")

summary = st.session_state.get("evaluation_summary")

if summary is not None:
    st.subheader("Evaluation metrics")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tickets", summary["ticket_count"])
    c2.metric("Category accuracy", f'{summary["category_accuracy"]:.0%}')
    c3.metric("Order ID accuracy", f'{summary["order_id_accuracy"]:.0%}')
    c4.metric("Lookup accuracy", f'{summary["lookup_accuracy"]:.0%}')

    st.metric(
        "Overall field accuracy",
        f'{summary["overall_field_accuracy"]:.1%}',
    )

    st.caption(
        f'Model: {st.session_state["evaluation_model"]}. '
        "Overall field accuracy weights the three fields equally."
    )

    st.subheader("Ticket-by-ticket results")

    for item in st.session_state["evaluation_details"]:
        with st.expander(f'{item["id"]}: {item["ticket"]}'):
            st.write("Expected")
            st.json(item["expected"])
            st.write("Predicted")
            st.json(item["predicted"])
            st.write("Field scores")
            st.json(item["scores"])

            st.write(f'Latency: {item["latency_ms"]:.2f} ms')
            st.write(f'Total tokens: {item["total_tokens"]}')

            if item["parse_error"]:
                st.warning(item["parse_error"])

