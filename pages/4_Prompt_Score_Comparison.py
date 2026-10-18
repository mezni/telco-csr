import streamlit as st
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from experiment_store import save_experiment
from llm_service import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT
from prompt_evaluation import run_prompt_evaluation

st.set_page_config(
    page_title="Prompt Score Comparison",
    page_icon="🧪",
    layout="wide",
)

st.title("Prompt Score Comparison")
st.caption(
    "Evaluate two prompts against the same dataset and compare "
    "accuracy, latency, and token usage."
)

# --------------------------------------------------
# Model configuration
# --------------------------------------------------

model = st.text_input(
    "Model",
    value=DEFAULT_MODEL,
    help="Use a model identifier supported by your API account.",
)

# --------------------------------------------------
# Prompt metadata
# --------------------------------------------------

st.subheader("Prompt metadata")

metadata_a, metadata_b = st.columns(2)

with metadata_a:
    prompt_name_a = st.text_input(
        "Prompt A name",
        value="baseline",
        key="prompt_name_a",
    )
    prompt_version_a = st.text_input(
        "Prompt A version",
        value="v1",
        key="prompt_version_a",
    )

with metadata_b:
    prompt_name_b = st.text_input(
        "Prompt B name",
        value="structured-json",
        key="prompt_name_b",
    )
    prompt_version_b = st.text_input(
        "Prompt B version",
        value="v1",
        key="prompt_version_b",
    )

# --------------------------------------------------
# Prompt editors
# --------------------------------------------------

st.subheader("System prompts")

prompt_a, prompt_b = st.columns(2)

with prompt_a:
    st.markdown("### Prompt A")
    system_prompt_a = st.text_area(
        "System prompt A",
        value=DEFAULT_SYSTEM_PROMPT,
        height=280,
        key="system_prompt_a",
    )

with prompt_b:
    st.markdown("### Prompt B")
    system_prompt_b = st.text_area(
        "System prompt B",
        value=(
            "You are a telecom customer support ticket classifier.\n"
            "Classify the customer's message into exactly one category:\n"
            "- order_status\n"
            "- billing\n"
            "- technical_support\n"
            "- other\n\n"
            "Extract the order ID as an integer when present; otherwise "
            "return null.\n"
            "Set needs_order_lookup to true only when the ticket concerns "
            "an order that needs to be looked up.\n\n"
            "Return only a valid JSON object with exactly these fields:\n"
            "{\n"
            '  "category": "order_status",\n'
            '  "order_id": 4821,\n'
            '  "needs_order_lookup": true\n'
            "}\n\n"
            "Do not include Markdown fences or explanatory text. "
            "Do not invent customer or account information."
        ),
        height=280,
        key="system_prompt_b",
    )

st.divider()

# --------------------------------------------------
# Run evaluation and save results
# --------------------------------------------------

if st.button(
    "Run comparison",
    type="primary",
    width="stretch",
):
    if not model.strip():
        st.error("Enter a model identifier.")
    elif not system_prompt_a.strip() or not system_prompt_b.strip():
        st.error("Both system prompts must be non-empty.")
    elif not prompt_name_a.strip() or not prompt_name_b.strip():
        st.error("Both prompt names must be non-empty.")
    elif not prompt_version_a.strip() or not prompt_version_b.strip():
        st.error("Both prompt versions must be non-empty.")
    else:
        try:
            with st.spinner(
                "Evaluating Prompt A and Prompt B. "
                "This makes real LLM API calls..."
            ):
                result_a = run_prompt_evaluation(
                    prompt=system_prompt_a,
                    model=model.strip(),
                )

                result_b = run_prompt_evaluation(
                    prompt=system_prompt_b,
                    model=model.strip(),
                )

            # Persist both results only after both evaluations succeed.
            run_a_id = save_experiment(
                system_prompt_a,
                result_a,
                prompt_name=prompt_name_a.strip(),
                prompt_version=prompt_version_a.strip(),
            )

            run_b_id = save_experiment(
                system_prompt_b,
                result_b,
                prompt_name=prompt_name_b.strip(),
                prompt_version=prompt_version_b.strip(),
            )

            st.session_state["score_comparison"] = {
                "a": result_a,
                "b": result_b,
                "run_a_id": run_a_id,
                "run_b_id": run_b_id,
                "name_a": prompt_name_a.strip(),
                "version_a": prompt_version_a.strip(),
                "name_b": prompt_name_b.strip(),
                "version_b": prompt_version_b.strip(),
            }

            st.success(
                f"Comparison completed and saved. "
                f"Experiment IDs: #{run_a_id} and #{run_b_id}."
            )

        except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
            st.error(f"Comparison failed: {exc}")

# --------------------------------------------------
# Display comparison results
# --------------------------------------------------

comparison = st.session_state.get("score_comparison")

if comparison:
    result_a = comparison["a"]
    result_b = comparison["b"]

    summary_a = result_a["summary"]
    summary_b = result_b["summary"]

    st.divider()
    st.subheader("Comparison results")

    st.caption(
        f"Saved experiments: #{comparison['run_a_id']} and "
        f"#{comparison['run_b_id']}"
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            f"### Prompt A: {comparison['name_a']} "
            f"({comparison['version_a']})"
        )
        st.metric(
            "Overall field accuracy",
            f"{summary_a['overall_field_accuracy']:.1%}",
        )

    with col_b:
        st.markdown(
            f"### Prompt B: {comparison['name_b']} "
            f"({comparison['version_b']})"
        )
        st.metric(
            "Overall field accuracy",
            f"{summary_b['overall_field_accuracy']:.1%}",
        )

    # All table values are strings to avoid mixed-type Arrow errors.
    metric_rows = [
        {
            "Metric": "Model",
            "Prompt A": str(result_a["model"]),
            "Prompt B": str(result_b["model"]),
        },
        {
            "Metric": "Tickets evaluated",
            "Prompt A": str(result_a["ticket_count"]),
            "Prompt B": str(result_b["ticket_count"]),
        },
        {
            "Metric": "Category accuracy",
            "Prompt A": f"{summary_a['category_accuracy']:.1%}",
            "Prompt B": f"{summary_b['category_accuracy']:.1%}",
        },
        {
            "Metric": "Order ID accuracy",
            "Prompt A": f"{summary_a['order_id_accuracy']:.1%}",
            "Prompt B": f"{summary_b['order_id_accuracy']:.1%}",
        },
        {
            "Metric": "Lookup accuracy",
            "Prompt A": f"{summary_a['lookup_accuracy']:.1%}",
            "Prompt B": f"{summary_b['lookup_accuracy']:.1%}",
        },
        {
            "Metric": "Overall field accuracy",
            "Prompt A": f"{summary_a['overall_field_accuracy']:.1%}",
            "Prompt B": f"{summary_b['overall_field_accuracy']:.1%}",
        },
        {
            "Metric": "Average latency (ms)",
            "Prompt A": f"{result_a['average_latency_ms']:.2f}",
            "Prompt B": f"{result_b['average_latency_ms']:.2f}",
        },
        {
            "Metric": "Input tokens",
            "Prompt A": str(result_a["total_input_tokens"]),
            "Prompt B": str(result_b["total_input_tokens"]),
        },
        {
            "Metric": "Output tokens",
            "Prompt A": str(result_a["total_output_tokens"]),
            "Prompt B": str(result_b["total_output_tokens"]),
        },
    ]

    st.dataframe(
        metric_rows,
        hide_index=True,
        width="stretch",
    )

    # --------------------------------------------------
    # Per-ticket results
    # --------------------------------------------------

    st.subheader("Per-ticket results")

    details_a = {
        item["id"]: item for item in result_a["details"]
    }
    details_b = {
        item["id"]: item for item in result_b["details"]
    }

    detail_rows = []

    for ticket_id in dict.fromkeys(
        list(details_a.keys()) + list(details_b.keys())
    ):
        item_a = details_a.get(ticket_id)
        item_b = details_b.get(ticket_id)

        detail_rows.append(
            {
                "Ticket ID": ticket_id,
                "Prompt A category": (
                    str(item_a["predicted"].get("category"))
                    if item_a
                    else "Not evaluated"
                ),
                "Prompt A correct": (
                    str(all(item_a["scores"].values()))
                    if item_a
                    else "N/A"
                ),
                "Prompt B category": (
                    str(item_b["predicted"].get("category"))
                    if item_b
                    else "Not evaluated"
                ),
                "Prompt B correct": (
                    str(all(item_b["scores"].values()))
                    if item_b
                    else "N/A"
                ),
            }
        )

    st.dataframe(
        detail_rows,
        hide_index=True,
        width="stretch",
    )

    # --------------------------------------------------
    # Interpretation
    # --------------------------------------------------

    st.subheader("Interpretation")

    accuracy_difference = (
        summary_b["overall_field_accuracy"]
        - summary_a["overall_field_accuracy"]
    )

    latency_difference = (
        result_b["average_latency_ms"]
        - result_a["average_latency_ms"]
    )

    if accuracy_difference > 0:
        st.write(
            f"Prompt B improved overall field accuracy by "
            f"{accuracy_difference:.1%} relative to Prompt A."
        )
    elif accuracy_difference < 0:
        st.write(
            f"Prompt B reduced overall field accuracy by "
            f"{abs(accuracy_difference):.1%} relative to Prompt A."
        )
    else:
        st.write("Both prompts achieved the same overall field accuracy.")

    if latency_difference > 0:
        st.write(
            f"Prompt B was {latency_difference:.2f} ms slower on average."
        )
    elif latency_difference < 0:
        st.write(
            f"Prompt B was {abs(latency_difference):.2f} ms faster on average."
        )
    else:
        st.write("Both prompts had the same average latency.")

    st.caption(
        "These results apply only to the evaluated dataset. "
        "Overall field accuracy weights category, order ID, and lookup "
        "correctness equally. Latency can vary with network conditions "
        "and model load."
    )
