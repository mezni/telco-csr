
import streamlit as st

from experiment_store import get_experiment, list_experiments

st.set_page_config(page_title="Experiment History", layout="wide")
st.title("Experiment History")

runs = list_experiments()

if not runs:
    st.info("No experiments saved yet. Run a prompt comparison first.")
    st.stop()

table_rows = [
    {
        "ID": run["id"],
        "Created (UTC)": run["created_at"],
        "Model": run["model"],
        "Tickets": run["ticket_count"],
        "Category accuracy": f'{run["category_accuracy"]:.1%}',
        "Order ID accuracy": f'{run["order_id_accuracy"]:.1%}',
        "Lookup accuracy": f'{run["lookup_accuracy"]:.1%}',
        "Overall accuracy": f'{run["overall_field_accuracy"]:.1%}',
        "Latency (ms)": f'{run["average_latency_ms"]:.2f}',
        "Input tokens": run["total_input_tokens"],
        "Output tokens": run["total_output_tokens"],
    }
    for run in runs
]

st.dataframe(table_rows, hide_index=True, width="stretch")

selected_id = st.selectbox(
    "Inspect an experiment",
    options=[run["id"] for run in runs],
)

selected = get_experiment(selected_id)

if selected:
    st.subheader(f'Experiment #{selected["id"]}')
    st.write(f'Model: {selected["model"]}')
    st.write(f'Created: {selected["created_at"]}')

    st.markdown("**System prompt**")
    st.code(selected["prompt"], language="text")

    st.markdown("**Per-ticket results**")
    for detail in selected["details"]:
        with st.expander(f'{detail["id"]}: {detail["ticket"]}'):
            st.write("Expected")
            st.json(detail["expected"])
            st.write("Predicted")
            st.json(detail["predicted"])
            st.write("Scores")
            st.json(detail["scores"])

            if detail.get("parse_error"):
                st.warning(detail["parse_error"])

