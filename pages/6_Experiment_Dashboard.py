import pandas as pd
import streamlit as st

from experiment_dashboard import prepare_dashboard_data
from experiment_store import list_experiments

st.set_page_config(
    page_title="Experiment Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Experiment Dashboard")
st.caption("Compare saved LLM experiments without making new API calls.")

experiments = list_experiments(limit=100)

if not experiments:
    st.info("No experiments saved yet. Run a prompt comparison first.")
    st.stop()

rows = prepare_dashboard_data(experiments)
df = pd.DataFrame(rows)

# Latest experiment
latest = df.iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Latest overall accuracy",
    f"{latest['Overall accuracy (%)']:.2f}%",
)

col2.metric(
    "Latest average latency",
    f"{latest['Average latency (ms)']:.2f} ms",
)

col3.metric(
    "Experiments saved",
    len(df),
)

st.divider()

st.subheader("Accuracy over experiments")

accuracy_chart = df.set_index("Experiment")[
    [
        "Category accuracy (%)",
        "Order ID accuracy (%)",
        "Lookup accuracy (%)",
        "Overall accuracy (%)",
    ]
]

st.line_chart(accuracy_chart, width="stretch")

st.subheader("Latency over experiments")

latency_chart = df.set_index("Experiment")[["Average latency (ms)"]]

st.line_chart(latency_chart, width="stretch")

st.subheader("Token usage")

token_chart = df.set_index("Experiment")[["Input tokens", "Output tokens"]]

st.bar_chart(token_chart, width="stretch")

st.subheader("Experiment details")

st.dataframe(
    df,
    hide_index=True,
    width="stretch",
)
