import time

import streamlit as st

from classifier import classify_ticket

st.set_page_config(page_title="Telco AI Lab", layout="wide")
st.title("Telco AI Lab")
st.subheader("Lesson 1: Function execution and latency")

message = st.text_input(
    "Enter a support ticket",
    value="My order #4821 has not arrived.",
)

if st.button("Run classifier", type="primary"):
    start = time.perf_counter()
    result = classify_ticket(message)
    elapsed_ms = (time.perf_counter() - start) * 1000

    st.session_state["last_result"] = result
    st.session_state["last_elapsed_ms"] = elapsed_ms

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    elapsed_ms = st.session_state["last_elapsed_ms"]

    col1, col2 = st.columns(2)

    col1.metric("Execution time", f"{elapsed_ms:.4f} ms")
    col2.metric("Order lookup needed", str(result["needs_order_lookup"]))

    st.subheader("Classification result")
    st.json(result)

    st.caption(
        "This measures local Python execution only, "
        "not an LLM call or external API request."
    )
