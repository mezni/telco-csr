
import streamlit as st

from llm_service import DEFAULT_MODEL, run_inference

st.set_page_config(
    page_title="Prompt Experiments",
    layout="wide",
)

st.title("Prompt Experiment Lab")
st.caption(
    "Compare two system prompts with the same model and input."
)

model = st.text_input("Model", value=DEFAULT_MODEL)

ticket = st.text_area(
    "Test ticket — shared by both experiments",
    value="My order #4821 has not arrived.",
)

prompt_a = st.text_area(
    "Prompt A — baseline",
    value=(
        "Classify this telecom support ticket into a category "
        "and explain why."
    ),
    height=180,
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
Return valid JSON with these fields:
category, order_id, needs_order_lookup, explanation.""",
    height=240,
)

if st.button("Run A/B comparison", type="primary"):
    if not model.strip() or not ticket.strip():
        st.warning("Enter both a model and a test ticket.")
    elif not prompt_a.strip() or not prompt_b.strip():
        st.warning("Both prompts must contain instructions.")
    else:
        try:
            with st.spinner("Running two real model requests..."):
                result_a = run_inference(
                    ticket=ticket,
                    system_prompt=prompt_a,
                    model=model.strip(),
                )
                result_b = run_inference(
                    ticket=ticket,
                    system_prompt=prompt_b,
                    model=model.strip(),
                )

            st.session_state["prompt_comparison"] = {
                "model": model.strip(),
                "ticket": ticket,
                "result_a": result_a,
                "result_b": result_b,
            }
        except Exception as exc:
            st.error(f"Comparison failed: {exc}")

comparison = st.session_state.get("prompt_comparison")

if comparison:
    st.subheader("Results")

    col_a, col_b = st.columns(2)

    for col, label, key in [
        (col_a, "Prompt A — baseline", "result_a"),
        (col_b, "Prompt B — structured", "result_b"),
    ]:
        result = comparison[key]

        with col:
            st.markdown(f"### {label}")
            st.write(result["response"])
            st.metric("Latency", f'{result["latency_ms"]:.2f} ms')

            m1, m2 = st.columns(2)
            m1.metric("Input tokens", result["input_tokens"])
            m2.metric("Output tokens", result["output_tokens"])

    a = comparison["result_a"]
    b = comparison["result_b"]


    st.subheader("Metric comparison")

    metric_rows = [
        {
            "Metric": "Model",
            "Prompt A": str(a["model"]),
            "Prompt B": str(b["model"]),
        },
        {
            "Metric": "Latency (ms)",
            "Prompt A": f'{a["latency_ms"]:.2f}',
            "Prompt B": f'{b["latency_ms"]:.2f}',
        },
        {
            "Metric": "Input tokens",
            "Prompt A": str(a["input_tokens"]),
            "Prompt B": str(b["input_tokens"]),
        },
        {
            "Metric": "Output tokens",
            "Prompt A": str(a["output_tokens"]),
            "Prompt B": str(b["output_tokens"]),
        },
        {
            "Metric": "Total tokens",
            "Prompt A": str(a["total_tokens"]),
            "Prompt B": str(b["total_tokens"]),
        },
    ]

    st.dataframe(
        metric_rows,
        hide_index=True,
        width="stretch",
    )

    st.dataframe(metric_rows, hide_index=True, use_container_width=True)

    st.caption(
        "These are two individual runs. Latency varies between requests; "
        "one comparison does not establish which prompt is consistently better."
    )

