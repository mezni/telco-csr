import streamlit as st
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from experiment_store import save_experiment
from llm_service import DEFAULT_MODEL
from prompt_evaluation import run_prompt_evaluation

st.set_page_config(
    page_title="Prompt Score Comparison",
    layout="wide",
)

st.title("Prompt Score Comparison")
st.caption("Evaluate two prompts against the same labeled tickets.")

model = st.text_input("Model", value=DEFAULT_MODEL)

prompt_a = st.text_area(
    "Prompt A — baseline",
    value=(
        "Classify this telecom support ticket into a category "
        "and explain why."
    ),
    height=150,
)

prompt_b = st.text_area(
    "Prompt B — structured",
    value="""You classify telecom support tickets.

Choose one category:
- order_status
- billing
- technical_support
- other

Extract an order ID if present. Do not invent missing information.
Indicate whether an order lookup is needed.

Return one valid JSON object with exactly these fields:
category, order_id, needs_order_lookup.

Use an integer for order_id, or null if no ID is present.
Use true or false for needs_order_lookup.
Return JSON only, without Markdown fences.""",
    height=240,
)

if st.button("Evaluate both prompts", type="primary"):
    if not model.strip():
        st.warning("Enter a model name.")
    elif not prompt_a.strip() or not prompt_b.strip():
        st.warning("Both prompts are required.")
    else:
        try:
            with st.spinner(
                "Evaluating Prompt A and Prompt B on all tickets..."
            ):
                result_a = run_prompt_evaluation(
                    prompt=prompt_a,
                    model=model.strip(),
                )
                result_b = run_prompt_evaluation(
                    prompt=prompt_b,
                    model=model.strip(),
                )
                run_a_id = save_experiment(prompt_a, result_a)
                run_b_id = save_experiment(prompt_b, result_b)

            st.session_state["score_comparison"] = {
                "a": result_a,
                "b": result_b,
            }
            st.success("Comparison completed.")

        except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
            st.error(f"Evaluation failed: {exc}")

comparison = st.session_state.get("score_comparison")

if comparison:
    a = comparison["a"]
    b = comparison["b"]

    st.subheader("Accuracy comparison")

    rows = [
        {
            "Metric": "Category accuracy",
            "Prompt A": f'{a["summary"]["category_accuracy"]:.1%}',
            "Prompt B": f'{b["summary"]["category_accuracy"]:.1%}',
        },
        {
            "Metric": "Order ID accuracy",
            "Prompt A": f'{a["summary"]["order_id_accuracy"]:.1%}',
            "Prompt B": f'{b["summary"]["order_id_accuracy"]:.1%}',
        },
        {
            "Metric": "Lookup accuracy",
            "Prompt A": f'{a["summary"]["lookup_accuracy"]:.1%}',
            "Prompt B": f'{b["summary"]["lookup_accuracy"]:.1%}',
        },
        {
            "Metric": "Overall field accuracy",
            "Prompt A": f'{a["summary"]["overall_field_accuracy"]:.1%}',
            "Prompt B": f'{b["summary"]["overall_field_accuracy"]:.1%}',
        },
        {
            "Metric": "Average latency (ms)",
            "Prompt A": f'{a["average_latency_ms"]:.2f}',
            "Prompt B": f'{b["average_latency_ms"]:.2f}',
        },
        {
            "Metric": "Total input tokens",
            "Prompt A": str(a["total_input_tokens"]),
            "Prompt B": str(b["total_input_tokens"]),
        },
        {
            "Metric": "Total output tokens",
            "Prompt A": str(a["total_output_tokens"]),
            "Prompt B": str(b["total_output_tokens"]),
        },
    ]

    st.dataframe(rows, hide_index=True, width="stretch")

    st.subheader("Ticket-level comparison")

    for index, item_a in enumerate(a["details"]):
        item_b = b["details"][index]

        with st.expander(
            f'{item_a["id"]}: {item_a["ticket"]}'
        ):
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Prompt A**")
                st.json(item_a["predicted"])
                st.json(item_a["scores"])
                if item_a["parse_error"]:
                    st.warning(item_a["parse_error"])

            with col_b:
                st.markdown("**Prompt B**")
                st.json(item_b["predicted"])
                st.json(item_b["scores"])
                if item_b["parse_error"]:
                    st.warning(item_b["parse_error"])

    st.caption(
        "This is a small evaluation sample. Compare accuracy and cost "
        "before choosing a prompt; a single run does not establish "
        "reliable latency performance."
    )
    st.success("Comparison completed and saved to SQLite.")
    st.write(f"Prompt A experiment ID: {run_a_id}")
    st.write(f"Prompt B experiment ID: {run_b_id}")
