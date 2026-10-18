
import pandas as pd
import streamlit as st
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from experiment_store import get_experiment, list_experiments

st.set_page_config(
    page_title="Experiment History",
    page_icon="📚",
    layout="wide",
)

st.title("Experiment History")
st.write(
    "Review saved prompt evaluations, compare historical metrics, "
    "and inspect the metadata needed to reproduce an experiment."
)

# -------------------------------------------------------------------
# Load saved experiments
# -------------------------------------------------------------------

try:
    experiments = list_experiments(limit=100)
except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
    st.error(f"Could not load experiment history: {exc}")
    st.stop()

if not experiments:
    st.info(
        "No experiments have been saved yet. "
        "Run an evaluation from the Prompt Score Comparison page first."
    )
    st.stop()

# -------------------------------------------------------------------
# Experiment overview
# -------------------------------------------------------------------

overview_rows = []

for experiment in experiments:
    overview_rows.append(
        {
            "ID": experiment["id"],
            "Created at": experiment["created_at"],
            "Prompt": experiment.get("prompt_name", "unnamed"),
            "Version": experiment.get("prompt_version", "v1"),
            "Model": experiment["model"],
            "Tickets": experiment["ticket_count"],
            "Category accuracy": experiment["category_accuracy"],
            "Order ID accuracy": experiment["order_id_accuracy"],
            "Lookup accuracy": experiment["lookup_accuracy"],
            "Overall accuracy": experiment["overall_field_accuracy"],
            "Average latency (ms)": experiment["average_latency_ms"],
            "Input tokens": experiment["total_input_tokens"],
            "Output tokens": experiment["total_output_tokens"],
        }
    )

st.subheader("Saved experiments")

st.dataframe(
    pd.DataFrame(overview_rows),
    hide_index=True,
    width="stretch",
)

# -------------------------------------------------------------------
# Select an experiment
# -------------------------------------------------------------------

experiment_options = {
    (
        f"#{item['id']} — "
        f"{item.get('prompt_name', 'unnamed')} "
        f"({item.get('prompt_version', 'v1')}) — "
        f"{item['created_at']}"
    ): item["id"]
    for item in experiments
}

selected_label = st.selectbox(
    "Select an experiment to inspect",
    options=list(experiment_options.keys()),
)

selected_id = experiment_options[selected_label]

try:
    experiment = get_experiment(selected_id)
except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
    st.error(f"Could not load experiment #{selected_id}: {exc}")
    st.stop()

if experiment is None:
    st.warning("The selected experiment could not be found.")
    st.stop()

# -------------------------------------------------------------------
# Experiment details
# -------------------------------------------------------------------

st.divider()
st.header(f"Experiment #{experiment['id']}")

st.caption(
    f"Created: {experiment['created_at']} | "
    f"Model: {experiment['model']}"
)

metadata_col1, metadata_col2, metadata_col3 = st.columns(3)

with metadata_col1:
    st.metric("Prompt name", experiment.get("prompt_name", "unnamed"))

with metadata_col2:
    st.metric("Prompt version", experiment.get("prompt_version", "v1"))

with metadata_col3:
    st.metric("Tickets evaluated", experiment["ticket_count"])

st.subheader("Evaluation metrics")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric(
        "Category accuracy",
        f"{experiment['category_accuracy']:.1%}",
    )

with metric_col2:
    st.metric(
        "Order ID accuracy",
        f"{experiment['order_id_accuracy']:.1%}",
    )

with metric_col3:
    st.metric(
        "Lookup accuracy",
        f"{experiment['lookup_accuracy']:.1%}",
    )

with metric_col4:
    st.metric(
        "Overall field accuracy",
        f"{experiment['overall_field_accuracy']:.1%}",
    )

performance_col1, performance_col2, performance_col3 = st.columns(3)

with performance_col1:
    st.metric(
        "Average latency",
        f"{experiment['average_latency_ms']:.2f} ms",
    )

with performance_col2:
    st.metric(
        "Total input tokens",
        f"{experiment['total_input_tokens']:,}",
    )

with performance_col3:
    st.metric(
        "Total output tokens",
        f"{experiment['total_output_tokens']:,}",
    )

# -------------------------------------------------------------------
# Saved prompt
# -------------------------------------------------------------------

with st.expander("View saved system prompt"):
    st.code(experiment["prompt"], language="text")
    st.caption("SHA-256 fingerprint of the saved prompt")

    prompt_hash = experiment.get("prompt_hash", "")

    if prompt_hash:
        st.code(prompt_hash, language="text")
    else:
        st.info("No prompt hash was stored for this experiment.")

# -------------------------------------------------------------------
# Reproducibility manifest
# -------------------------------------------------------------------

st.subheader("Reproducibility manifest")

manifest = experiment.get("manifest", {})

if manifest:
    st.json(manifest)

    manifest_prompt_hash = manifest.get("prompt_hash")
    stored_prompt_hash = experiment.get("prompt_hash")

    if manifest_prompt_hash and stored_prompt_hash:
        if manifest_prompt_hash == stored_prompt_hash:
            st.success("Manifest prompt hash matches the stored prompt hash.")
        else:
            st.warning(
                "The manifest prompt hash differs from the stored prompt hash."
            )
else:
    st.info(
        "This experiment predates reproducibility metadata or has no "
        "manifest saved."
    )

# -------------------------------------------------------------------
# Per-ticket results
# -------------------------------------------------------------------

st.subheader("Per-ticket results")

details = experiment.get("details", [])

if not details:
    st.info("No per-ticket evaluation details were saved.")
else:
    ticket_rows = []

    for item in details:
        expected = item.get("expected", {})
        predicted = item.get("predicted", {})
        scores = item.get("scores", {})

        ticket_rows.append(
            {
                "Ticket ID": item.get("id", ""),
                "Ticket": item.get("ticket", ""),
                "Expected category": expected.get("category"),
                "Predicted category": predicted.get("category"),
                "Category correct": scores.get("category_correct", False),
                "Expected order ID": expected.get("order_id"),
                "Predicted order ID": predicted.get("order_id"),
                "Order ID correct": scores.get("order_id_correct", False),
                "Expected lookup": expected.get("needs_order_lookup"),
                "Predicted lookup": predicted.get("needs_order_lookup"),
                "Lookup correct": scores.get("lookup_correct", False),
                "Latency (ms)": item.get("latency_ms"),
                "Total tokens": item.get("total_tokens"),
                "Parse error": item.get("parse_error") or "",
            }
        )

    st.dataframe(
        pd.DataFrame(ticket_rows),
        hide_index=True,
        width="stretch",
    )

    incorrect_rows = [
        row
        for row in ticket_rows
        if not (
            row["Category correct"]
            and row["Order ID correct"]
            and row["Lookup correct"]
        )
    ]

    st.subheader("Incorrect or partially correct predictions")

    if incorrect_rows:
        st.dataframe(
            pd.DataFrame(incorrect_rows),
            hide_index=True,
            width="stretch",
        )
    else:
        st.success("All saved ticket predictions were correct.")

# -------------------------------------------------------------------
# Export saved experiment details
# -------------------------------------------------------------------

st.subheader("Export")

export_data = {
    "experiment_id": experiment["id"],
    "created_at": experiment["created_at"],
    "model": experiment["model"],
    "prompt_name": experiment.get("prompt_name", "unnamed"),
    "prompt_version": experiment.get("prompt_version", "v1"),
    "prompt": experiment["prompt"],
    "prompt_hash": experiment.get("prompt_hash", ""),
    "manifest": manifest,
    "ticket_count": experiment["ticket_count"],
    "metrics": {
        "category_accuracy": experiment["category_accuracy"],
        "order_id_accuracy": experiment["order_id_accuracy"],
        "lookup_accuracy": experiment["lookup_accuracy"],
        "overall_field_accuracy": experiment["overall_field_accuracy"],
        "average_latency_ms": experiment["average_latency_ms"],
        "total_input_tokens": experiment["total_input_tokens"],
        "total_output_tokens": experiment["total_output_tokens"],
    },
    "details": details,
}

st.download_button(
    label="Download experiment as JSON",
    data=pd.io.json.dumps(export_data, indent=2),
    file_name=f"experiment_{experiment['id']}.json",
    mime="application/json",
)

