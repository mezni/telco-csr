
import pandas as pd
import streamlit as st
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from evaluator import load_dataset
from experiment_store import save_experiment
from llm_service import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT
from prompt_evaluation import run_prompt_evaluation
from reproducibility import build_manifest

st.set_page_config(
    page_title="Prompt Score Comparison",
    page_icon="🧪",
    layout="wide",
)

st.title("Prompt Score Comparison")
st.write(
    "Compare two prompt versions using the same evaluation dataset. "
    "Each run is saved with its prompt metadata and reproducibility manifest."
)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

model = st.text_input("Model", value=DEFAULT_MODEL.strip())

st.subheader("Prompt A")
prompt_name_a = st.text_input("Prompt A name", value="Baseline prompt")
prompt_version_a = st.text_input("Prompt A version", value="v1")
system_prompt_a = st.text_area(
    "Prompt A instructions",
    value=DEFAULT_SYSTEM_PROMPT.strip(),
    height=240,
)

st.subheader("Prompt B")
prompt_name_b = st.text_input("Prompt B name", value="Improved prompt")
prompt_version_b = st.text_input("Prompt B version", value="v2")
system_prompt_b = st.text_area(
    "Prompt B instructions",
    value=(
        "You are a telecom customer support ticket classifier.\n\n"
        "Classify each customer message into exactly one category:\n"
        "- order_status\n"
        "- billing\n"
        "- technical_support\n"
        "- other\n\n"
        "Return only valid JSON with these fields:\n"
        '- "category": one allowed category\n'
        '- "order_id": an integer if an order number is explicitly mentioned, '
        "otherwise null\n"
        '- "needs_order_lookup": true only when order information must be retrieved to answer the customer, otherwise false\n\n'
        "Do not invent customer or account information. "
        "Do not include Markdown fences or additional text."
    ),
    height=240,
)

st.divider()

# -------------------------------------------------------------------
# Run and save comparison
# -------------------------------------------------------------------

if st.button("Run and save comparison", type="primary"):
    if not model.strip():
        st.error("Enter a model name.")
        st.stop()

    if not system_prompt_a.strip() or not system_prompt_b.strip():
        st.error("Both prompts must contain instructions.")
        st.stop()

    if not prompt_name_a.strip() or not prompt_name_b.strip():
        st.error("Enter a name for each prompt.")
        st.stop()

    if not prompt_version_a.strip() or not prompt_version_b.strip():
        st.error("Enter a version for each prompt.")
        st.stop()

    try:
        with st.spinner("Loading evaluation dataset..."):
            dataset = load_dataset()

        if not dataset:
            st.error("The evaluation dataset is empty.")
            st.stop()

        with st.spinner("Evaluating Prompt A..."):
            result_a = run_prompt_evaluation(
                prompt=system_prompt_a,
                model=model.strip(),
                tickets=dataset,
            )

        with st.spinner("Evaluating Prompt B..."):
            result_b = run_prompt_evaluation(
                prompt=system_prompt_b,
                model=model.strip(),
                tickets=dataset,
            )

        # Build manifests from the same dataset used for each evaluation.
        manifest_a = build_manifest(
            prompt=system_prompt_a,
            model=model.strip(),
            dataset=dataset,
        )
        manifest_b = build_manifest(
            prompt=system_prompt_b,
            model=model.strip(),
            dataset=dataset,
        )

        experiment_id_a = save_experiment(
            prompt=system_prompt_a,
            result=result_a,
            prompt_name=prompt_name_a.strip(),
            prompt_version=prompt_version_a.strip(),
            manifest=manifest_a,
        )

        experiment_id_b = save_experiment(
            prompt=system_prompt_b,
            result=result_b,
            prompt_name=prompt_name_b.strip(),
            prompt_version=prompt_version_b.strip(),
            manifest=manifest_b,
        )

        st.session_state["prompt_comparison"] = {
            "result_a": result_a,
            "result_b": result_b,
            "experiment_id_a": experiment_id_a,
            "experiment_id_b": experiment_id_b,
            "prompt_name_a": prompt_name_a.strip(),
            "prompt_version_a": prompt_version_a.strip(),
            "prompt_name_b": prompt_name_b.strip(),
            "prompt_version_b": prompt_version_b.strip(),
            "manifest_a": manifest_a,
            "manifest_b": manifest_b,
        }

        st.success(
            f"Comparison saved. Experiment IDs: "
            f"A = {experiment_id_a}, B = {experiment_id_b}."
        )

    except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
        st.error(f"Comparison failed: {exc}")


# -------------------------------------------------------------------
# Display results from the most recent comparison
# -------------------------------------------------------------------

comparison = st.session_state.get("prompt_comparison")

if comparison:
    result_a = comparison["result_a"]
    result_b = comparison["result_b"]

    st.divider()
    st.header("Comparison Results")

    st.caption(
        f"Prompt A: {comparison['prompt_name_a']} "
        f"({comparison['prompt_version_a']}) — "
        f"experiment #{comparison['experiment_id_a']}"
    )
    st.caption(
        f"Prompt B: {comparison['prompt_name_b']} "
        f"({comparison['prompt_version_b']}) — "
        f"experiment #{comparison['experiment_id_b']}"
    )

    summary_a = result_a["summary"]
    summary_b = result_b["summary"]

    metric_rows = [
        {
            "Metric": "Category accuracy",
            "Prompt A": summary_a["category_accuracy"],
            "Prompt B": summary_b["category_accuracy"],
            "Difference (B - A)": (
                summary_b["category_accuracy"]
                - summary_a["category_accuracy"]
            ),
            "Direction": "Higher is better",
        },
        {
            "Metric": "Order ID accuracy",
            "Prompt A": summary_a["order_id_accuracy"],
            "Prompt B": summary_b["order_id_accuracy"],
            "Difference (B - A)": (
                summary_b["order_id_accuracy"]
                - summary_a["order_id_accuracy"]
            ),
            "Direction": "Higher is better",
        },
        {
            "Metric": "Lookup accuracy",
            "Prompt A": summary_a["lookup_accuracy"],
            "Prompt B": summary_b["lookup_accuracy"],
            "Difference (B - A)": (
                summary_b["lookup_accuracy"]
                - summary_a["lookup_accuracy"]
            ),
            "Direction": "Higher is better",
        },
        {
            "Metric": "Overall field accuracy",
            "Prompt A": summary_a["overall_field_accuracy"],
            "Prompt B": summary_b["overall_field_accuracy"],
            "Difference (B - A)": (
                summary_b["overall_field_accuracy"]
                - summary_a["overall_field_accuracy"]
            ),
            "Direction": "Higher is better",
        },
        {
            "Metric": "Average latency (ms)",
            "Prompt A": result_a["average_latency_ms"],
            "Prompt B": result_b["average_latency_ms"],
            "Difference (B - A)": (
                result_b["average_latency_ms"]
                - result_a["average_latency_ms"]
            ),
            "Direction": "Lower is better",
        },
        {
            "Metric": "Total input tokens",
            "Prompt A": result_a["total_input_tokens"],
            "Prompt B": result_b["total_input_tokens"],
            "Difference (B - A)": (
                result_b["total_input_tokens"]
                - result_a["total_input_tokens"]
            ),
            "Direction": "Lower is generally cheaper",
        },
        {
            "Metric": "Total output tokens",
            "Prompt A": result_a["total_output_tokens"],
            "Prompt B": result_b["total_output_tokens"],
            "Difference (B - A)": (
                result_b["total_output_tokens"]
                - result_a["total_output_tokens"]
            ),
            "Direction": "Lower is generally cheaper",
        },
    ]

    st.dataframe(
        pd.DataFrame(metric_rows),
        hide_index=True,
        width="stretch",
    )

    # Per-ticket comparison
    st.subheader("Per-ticket results")

    details_a = {
        item["id"]: item for item in result_a.get("details", [])
    }
    details_b = {
        item["id"]: item for item in result_b.get("details", [])
    }

    ticket_rows = []

    for ticket_id in sorted(set(details_a) | set(details_b)):
        item_a = details_a.get(ticket_id, {})
        item_b = details_b.get(ticket_id, {})

        predicted_a = item_a.get("predicted", {})
        predicted_b = item_b.get("predicted", {})
        scores_a = item_a.get("scores", {})
        scores_b = item_b.get("scores", {})

        ticket_rows.append(
            {
                "Ticket ID": ticket_id,
                "Ticket": item_a.get("ticket", item_b.get("ticket", "")),
                "Expected category": item_a.get("expected", {}).get(
                    "category", ""
                ),
                "A category": predicted_a.get("category", "INVALID"),
                "B category": predicted_b.get("category", "INVALID"),
                "A category correct": scores_a.get(
                    "category_correct", False
                ),
                "B category correct": scores_b.get(
                    "category_correct", False
                ),
                "A order ID": predicted_a.get("order_id"),
                "B order ID": predicted_b.get("order_id"),
                "A lookup correct": scores_a.get("lookup_correct", False),
                "B lookup correct": scores_b.get("lookup_correct", False),
                "A JSON error": item_a.get("parse_error") or "",
                "B JSON error": item_b.get("parse_error") or "",
            }
        )

    st.dataframe(
        pd.DataFrame(ticket_rows),
        hide_index=True,
        width="stretch",
    )

    # Reproducibility information
    st.subheader("Reproducibility manifests")

    with st.expander("Prompt A manifest"):
        st.json(comparison["manifest_a"])

    with st.expander("Prompt B manifest"):
        st.json(comparison["manifest_b"])

