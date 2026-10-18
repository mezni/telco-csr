import pandas as pd
import streamlit as st

from error_analysis import analyze_errors
from experiment_store import get_experiment, list_experiments

st.set_page_config(
    page_title="Error Analysis",
    page_icon="🔎",
    layout="wide",
)

st.title("Error Analysis")
st.caption(
    "Find weak ticket categories and inspect incorrect predictions "
    "from saved LLM evaluations."
)

experiments = list_experiments(limit=100)

if not experiments:
    st.info("No saved experiments yet. Run a prompt comparison first.")
    st.stop()

options = {
    (
        f"#{item['id']} — {item.get('prompt_name', 'unnamed')} "
        f"{item.get('prompt_version', '')} — {item['model']}"
    ): item["id"]
    for item in experiments
}

selected_label = st.selectbox(
    "Select an experiment",
    list(options.keys()),
)

if st.button("Analyze errors", type="primary"):
    experiment = get_experiment(options[selected_label])

    if experiment is None:
        st.error("Could not load the selected experiment.")
    else:
        analysis = analyze_errors(experiment.get("details", []))
        st.session_state["error_analysis_result"] = {
            "experiment_id": experiment["id"],
            "analysis": analysis,
        }

saved = st.session_state.get("error_analysis_result")

if saved:
    analysis = saved["analysis"]

    st.subheader(f"Experiment #{saved['experiment_id']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Tickets analyzed", analysis["ticket_count"])
    col2.metric("Tickets with errors", analysis["error_count"])

    if analysis["ticket_count"]:
        error_rate = analysis["error_count"] / analysis["ticket_count"]
        col3.metric("Ticket error rate", f"{error_rate:.1%}")
    else:
        col3.metric("Ticket error rate", "N/A")

    st.divider()
    st.subheader("Performance by expected category")

    summary = analysis["category_summary"]

    if not summary:
        st.info("This experiment has no ticket-level results.")
    else:
        rows = []

        for category, stats in sorted(summary.items()):
            rows.append(
                {
                    "Category": category,
                    "Tickets": stats["ticket_count"],
                    "Category accuracy": (f"{stats['category_accuracy']:.1%}"),
                    "Order ID accuracy": (f"{stats['order_id_accuracy']:.1%}"),
                    "Lookup accuracy": (f"{stats['lookup_accuracy']:.1%}"),
                    "Overall field accuracy": (
                        f"{stats['overall_field_accuracy']:.1%}"
                    ),
                    "Tickets with errors": stats["error_count"],
                }
            )

        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
        )

        chart_data = pd.DataFrame(
            [
                {
                    "Category": category,
                    "Category accuracy": stats["category_accuracy"],
                    "Order ID accuracy": stats["order_id_accuracy"],
                    "Lookup accuracy": stats["lookup_accuracy"],
                }
                for category, stats in sorted(summary.items())
            ]
        ).set_index("Category")

        st.subheader("Accuracy by category")
        st.bar_chart(chart_data, width="stretch")

    st.divider()
    st.subheader("Incorrect predictions")

    if not analysis["errors"]:
        st.success("No incorrect tickets were found in this experiment.")
    else:
        error_rows = []

        for error in analysis["errors"]:
            error_rows.append(
                {
                    "Ticket ID": error["id"],
                    "Ticket": error["ticket"],
                    "Expected category": error["expected_category"],
                    "Predicted category": error["predicted_category"],
                    "Expected order ID": str(error["expected_order_id"]),
                    "Predicted order ID": str(error["predicted_order_id"]),
                    "Expected lookup": str(error["expected_lookup"]),
                    "Predicted lookup": str(error["predicted_lookup"]),
                    "Category correct": str(error["category_correct"]),
                    "Order ID correct": str(error["order_id_correct"]),
                    "Lookup correct": str(error["lookup_correct"]),
                    "Parse error": error["parse_error"] or "",
                }
            )

        st.dataframe(
            error_rows,
            hide_index=True,
            width="stretch",
        )

        st.markdown("### Review individual errors")

        for error in analysis["errors"]:
            with st.expander(f"{error['id']} — {error['expected_category']}"):
                st.write("**Customer message:**", error["ticket"])
                st.write(
                    "**Expected:**",
                    error["expected_category"],
                    "| Order ID:",
                    error["expected_order_id"],
                    "| Lookup:",
                    error["expected_lookup"],
                )
                st.write(
                    "**Predicted:**",
                    error["predicted_category"],
                    "| Order ID:",
                    error["predicted_order_id"],
                    "| Lookup:",
                    error["predicted_lookup"],
                )

                failed_fields = [
                    field
                    for field in (
                        "category_correct",
                        "order_id_correct",
                        "lookup_correct",
                    )
                    if not error[field]
                ]

                st.write(
                    "**Fields to investigate:**",
                    ", ".join(failed_fields),
                )

                if error["parse_error"]:
                    st.warning(error["parse_error"])
