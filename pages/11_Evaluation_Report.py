import streamlit as st
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from evaluation_report import build_evaluation_report
from experiment_store import get_experiment, list_experiments

st.set_page_config(
    page_title="Evaluation Report",
    page_icon="📋",
    layout="wide",
)

st.title("Evaluation Report")
st.write(
    "Generate a report from a saved ticket-classification experiment, "
    "including accuracy, error analysis, reproducibility, cost, and gates."
)

try:
    experiments = list_experiments(limit=100)
except (
    APIError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
    RuntimeError,
    ValueError,
    TypeError,
) as exc:
    st.error(f"Could not load experiment history: {exc}")
    st.stop()

if not experiments:
    st.info("Run and save an evaluation before generating a report.")
    st.stop()

experiment_options = {
    (
        f"#{item['id']} — "
        f"{item.get('prompt_name', 'unnamed')} "
        f"({item.get('prompt_version', 'v1')}) — "
        f"{item['model']}"
    ): item["id"]
    for item in experiments
}

selected_label = st.selectbox(
    "Select saved experiment",
    options=list(experiment_options.keys()),
)

selected_id = experiment_options[selected_label]

try:
    experiment = get_experiment(selected_id)
except (
    APIError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
    RuntimeError,
    ValueError,
    TypeError,
) as exc:
    st.error(f"Could not load experiment: {exc}")
    st.stop()

if experiment is None:
    st.error("The selected experiment was not found.")
    st.stop()

st.subheader("Cost configuration")

cost_col1, cost_col2 = st.columns(2)

with cost_col1:
    input_rate = st.number_input(
        "Input price (USD per 1M tokens)",
        min_value=0.0,
        value=0.0,
        step=0.1,
        format="%.6f",
    )

with cost_col2:
    output_rate = st.number_input(
        "Output price (USD per 1M tokens)",
        min_value=0.0,
        value=0.0,
        step=0.1,
        format="%.6f",
    )

st.subheader("Evaluation gates")

gate_col1, gate_col2 = st.columns(2)

with gate_col1:
    min_overall_accuracy = st.slider(
        "Minimum overall field accuracy",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.01,
    )

    min_category_accuracy = st.slider(
        "Minimum category accuracy",
        min_value=0.0,
        max_value=1.0,
        value=0.90,
        step=0.01,
    )

with gate_col2:
    max_latency_ms = st.number_input(
        "Maximum average latency (ms)",
        min_value=0.0,
        value=2000.0,
        step=100.0,
    )

    max_invalid_json = st.number_input(
        "Maximum invalid JSON responses",
        min_value=0,
        value=0,
        step=1,
    )

if st.button("Generate report", type="primary"):
    try:
        report = build_evaluation_report(
            experiment=experiment,
            input_price_per_million=input_rate,
            output_price_per_million=output_rate,
            min_overall_accuracy=min_overall_accuracy,
            min_category_accuracy=min_category_accuracy,
            max_latency_ms=max_latency_ms,
            max_invalid_json=int(max_invalid_json),
        )

        st.session_state["evaluation_report"] = report
        st.session_state["evaluation_report_experiment_id"] = selected_id

    except (
        APIError,
        AuthenticationError,
        OpenAIError,
        RateLimitError,
        RuntimeError,
        ValueError,
        TypeError,
    ) as exc:
        st.error(f"Could not generate report: {exc}")

report = st.session_state.get("evaluation_report")
report_experiment_id = st.session_state.get("evaluation_report_experiment_id")

if report and report_experiment_id == selected_id:
    st.divider()
    st.subheader("Report preview")

    st.markdown(report)

    st.download_button(
        label="Download Markdown report",
        data=report,
        file_name=f"ticket_triage_evaluation_{selected_id}.md",
        mime="text/markdown",
    )
