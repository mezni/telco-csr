import streamlit as st

from evaluation_gates import evaluate_gates
from experiment_store import get_experiment, list_experiments

st.set_page_config(
    page_title="Evaluation Gates",
    page_icon="🚦",
    layout="wide",
)

st.title("Evaluation Gates")
st.caption(
    "Check saved experiment results against quality and performance "
    "requirements without making new API calls."
)

experiments = list_experiments(limit=100)

if not experiments:
    st.info("No experiments saved yet. Run a prompt comparison first.")
    st.stop()

options = {
    (
        f"#{item['id']} — {item.get('prompt_name', 'unnamed')} "
        f"{item.get('prompt_version', '')} — {item['model']}"
    ): item["id"]
    for item in experiments
}

selected_label = st.selectbox(
    "Experiment to evaluate",
    list(options.keys()),
)

st.subheader("Acceptance thresholds")

col1, col2 = st.columns(2)

with col1:
    min_overall_accuracy = st.slider(
        "Minimum overall field accuracy",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.05,
        format="%.0f%%",
    )

    min_category_accuracy = st.slider(
        "Minimum category accuracy",
        min_value=0.0,
        max_value=1.0,
        value=0.90,
        step=0.05,
        format="%.0f%%",
    )

with col2:
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

if st.button("Evaluate gates", type="primary"):
    experiment_id = options[selected_label]
    experiment = get_experiment(experiment_id)

    if experiment is None:
        st.error("The selected experiment could not be loaded.")
    else:
        result = evaluate_gates(
            experiment,
            min_overall_accuracy=min_overall_accuracy,
            min_category_accuracy=min_category_accuracy,
            max_latency_ms=max_latency_ms,
            max_invalid_json=max_invalid_json,
        )

        st.session_state["gate_result"] = {
            "experiment_id": experiment_id,
            "result": result,
        }

saved_result = st.session_state.get("gate_result")

if saved_result:
    result = saved_result["result"]

    st.divider()
    st.subheader(f"Gate results for experiment #{saved_result['experiment_id']}")

    if result["approved"]:
        st.success("All configured evaluation gates passed.")
    else:
        st.error("Evaluation rejected. Failed gates: " + ", ".join(result["failures"]))

    rows = []

    for name, check in result["checks"].items():
        rows.append(
            {
                "Gate": name,
                "Actual": str(check["actual"]),
                "Threshold": str(check["threshold"]),
                "Result": "PASS" if check["passed"] else "FAIL",
            }
        )

    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
    )

    st.caption(
        "Passing these gates is an evaluation result, not an automatic "
        "production approval. Review dataset coverage and individual "
        "ticket errors before deploying a prompt."
    )
