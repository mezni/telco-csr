
import pandas as pd
import streamlit as st
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from cost_analysis import analyze_experiment
from experiment_store import get_experiment, list_experiments

st.set_page_config(
    page_title="Cost & Performance",
    page_icon="💰",
    layout="wide",
)

st.title("Cost & Performance Analysis")
st.write(
    "Estimate token costs and analyze latency for saved experiments. "
    "Enter the pricing rates that apply to your model and account."
)

st.caption(
    "Prices are user-supplied USD per million tokens. "
    "These calculations estimate token charges only."
)

# -------------------------------------------------------------------
# Pricing configuration
# -------------------------------------------------------------------

price_col1, price_col2 = st.columns(2)

with price_col1:
    input_rate = st.number_input(
        "Input price (USD per 1M tokens)",
        min_value=0.0,
        value=0.0,
        step=0.1,
        format="%.6f",
    )

with price_col2:
    output_rate = st.number_input(
        "Output price (USD per 1M tokens)",
        min_value=0.0,
        value=0.0,
        step=0.1,
        format="%.6f",
    )

st.info(
    "Look up the applicable model pricing from your provider and enter "
    "the rates above. A rate of $0.00 is treated as a zero-cost assumption, "
    "not confirmation that usage is free."
)

# -------------------------------------------------------------------
# Load experiments
# -------------------------------------------------------------------

try:
    experiments = list_experiments(limit=100)
except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
    st.error(f"Could not load experiments: {exc}")
    st.stop()

if not experiments:
    st.info("No saved experiments found. Run an evaluation first.")
    st.stop()

labels = {
    (
        f"#{item['id']} — "
        f"{item.get('prompt_name', 'unnamed')} "
        f"({item.get('prompt_version', 'v1')}) — "
        f"{item['model']}"
    ): item["id"]
    for item in experiments
}

selected_label = st.selectbox(
    "Select experiment",
    options=list(labels.keys()),
)

selected_id = labels[selected_label]

try:
    experiment = get_experiment(selected_id)
except (APIError, AuthenticationError, OpenAIError, RateLimitError, RuntimeError, ValueError, TypeError) as exc:
    st.error(f"Could not load experiment details: {exc}")
    st.stop()

if experiment is None:
    st.error("The selected experiment was not found.")
    st.stop()

# -------------------------------------------------------------------
# Calculate cost and performance
# -------------------------------------------------------------------

analysis = analyze_experiment(
    experiment=experiment,
    input_price_per_million=input_rate,
    output_price_per_million=output_rate,
)

st.divider()
st.subheader("Estimated cost")

cost_col1, cost_col2, cost_col3 = st.columns(3)

with cost_col1:
    st.metric(
        "Input cost",
        f"${analysis['input_cost_usd']:.6f}",
    )

with cost_col2:
    st.metric(
        "Output cost",
        f"${analysis['output_cost_usd']:.6f}",
    )

with cost_col3:
    st.metric(
        "Total estimated cost",
        f"${analysis['total_cost_usd']:.6f}",
    )

st.metric(
    "Estimated cost per ticket",
    f"${analysis['cost_per_ticket_usd']:.6f}",
)

st.caption(
    f"{experiment['ticket_count']} tickets | "
    f"{experiment['total_input_tokens']:,} input tokens | "
    f"{experiment['total_output_tokens']:,} output tokens"
)

st.divider()
st.subheader("Latency")

latency_col1, latency_col2, latency_col3 = st.columns(3)

with latency_col1:
    st.metric(
        "Saved average latency",
        f"{experiment['average_latency_ms']:.2f} ms",
    )

with latency_col2:
    st.metric(
        "Median latency",
        f"{analysis['median_latency_ms']:.2f} ms",
    )

with latency_col3:
    st.metric(
        "P95 latency",
        f"{analysis['p95_latency_ms']:.2f} ms",
    )

st.caption(
    "Median and P95 use per-ticket latency measurements saved with this "
    "experiment. Average latency above uses the experiment's saved summary."
)

# -------------------------------------------------------------------
# Accuracy and cost context
# -------------------------------------------------------------------

st.divider()
st.subheader("Accuracy and efficiency")

accuracy_col1, accuracy_col2, accuracy_col3 = st.columns(3)

with accuracy_col1:
    st.metric(
        "Category accuracy",
        f"{experiment['category_accuracy']:.1%}",
    )

with accuracy_col2:
    st.metric(
        "Order ID accuracy",
        f"{experiment['order_id_accuracy']:.1%}",
    )

with accuracy_col3:
    st.metric(
        "Lookup accuracy",
        f"{experiment['lookup_accuracy']:.1%}",
    )

summary = pd.DataFrame(
    [
        {
            "Metric": "Estimated total cost (USD)",
            "Value": analysis["total_cost_usd"],
        },
        {
            "Metric": "Estimated cost per ticket (USD)",
            "Value": analysis["cost_per_ticket_usd"],
        },
        {
            "Metric": "Total tokens",
            "Value": analysis["total_tokens"],
        },
        {
            "Metric": "Average latency (ms)",
            "Value": experiment["average_latency_ms"],
        },
        {
            "Metric": "Median latency (ms)",
            "Value": analysis["median_latency_ms"],
        },
        {
            "Metric": "P95 latency (ms)",
            "Value": analysis["p95_latency_ms"],
        },
        {
            "Metric": "Overall field accuracy",
            "Value": experiment["overall_field_accuracy"],
        },
    ]
)

st.dataframe(
    summary,
    hide_index=True,
    width="stretch",
)

st.subheader("Interpretation")

st.markdown(
    """
    - **Accuracy:** higher is better, but review each error category.
    - **Cost:** compare experiments using the same applicable price rates.
    - **Latency:** lower is generally better; P95 helps reveal slower cases.
    - **Trade-off:** do not select a prompt based on cost alone if it reduces
      classification quality or produces invalid JSON.
    """
)

