import streamlit as st

from experiment_comparison import compare_experiments
from experiment_store import get_experiment, list_experiments

st.set_page_config(
    page_title="Regression Checker",
    page_icon="🔍",
    layout="wide",
)

st.title("Prompt Regression Checker")
st.caption("Compare saved experiments without making new LLM calls.")

experiments = list_experiments(limit=100)

if len(experiments) < 2:
    st.info("Save at least two experiments before comparing them.")
    st.stop()

# list_experiments returns newest first.
experiment_options = {
    (
        f"#{item['id']} — {item.get('prompt_name', 'unnamed')} "
        f"{item.get('prompt_version', '')} — {item['model']}"
    ): item["id"]
    for item in experiments
}

labels = list(experiment_options)

baseline_label = st.selectbox(
    "Baseline experiment",
    labels,
    index=min(1, len(labels) - 1),
)

candidate_label = st.selectbox(
    "Candidate experiment",
    labels,
    index=0,
)

if st.button("Compare experiments", type="primary"):
    baseline_id = experiment_options[baseline_label]
    candidate_id = experiment_options[candidate_label]

    if baseline_id == candidate_id:
        st.error("Choose two different experiments.")
    else:
        baseline = get_experiment(baseline_id)
        candidate = get_experiment(candidate_id)

        if baseline is None or candidate is None:
            st.error("Could not load one of the selected experiments.")
        else:
            result = compare_experiments(baseline, candidate)
            st.session_state["regression_result"] = result

result = st.session_state.get("regression_result")

if result:
    st.subheader("Metric comparison")

    rows = []

    for metric, values in result["comparisons"].items():
        rows.append(
            {
                "Metric": metric,
                "Baseline": str(values["baseline"]),
                "Candidate": str(values["candidate"]),
                "Difference": str(round(values["difference"], 4)),
                "Improved": str(values["improved"]),
                "Regressed": str(values["regressed"]),
            }
        )

    st.dataframe(rows, hide_index=True, width="stretch")

    if result["regressions"]:
        st.warning(
            "Regressions detected: "
            + ", ".join(result["regressions"])
        )
    else:
        st.success("No regressions detected in the tracked metrics.")

    if result["improvements"]:
        st.write("Improvements:", ", ".join(result["improvements"]))
