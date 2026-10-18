import streamlit as st
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from llm_service import (
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    run_inference,
)

st.set_page_config(page_title="LLM Inference Lab", layout="wide")

st.title("LLM Inference Lab")
st.caption("Run a real model request and inspect its metrics.")

model = st.text_input("Model", value=DEFAULT_MODEL)

system_prompt = st.text_area(
    "System prompt",
    value=DEFAULT_SYSTEM_PROMPT,
    height=220,
)

ticket = st.text_area(
    "Customer ticket",
    value="My order #4821 has not arrived.",
    height=100,
)

if st.button("Run inference", type="primary"):
    if not ticket.strip():
        st.warning("Enter a customer ticket first.")
    elif not system_prompt.strip():
        st.warning("Enter a system prompt first.")
    elif not model.strip():
        st.warning("Enter a model name first.")
    else:
        try:
            with st.spinner("Waiting for the model..."):
                result = run_inference(
                    ticket=ticket,
                    system_prompt=system_prompt,
                    model=model.strip(),
                )
            st.session_state["llm_result"] = result
        except (
            APIError,
            AuthenticationError,
            OpenAIError,
            RateLimitError,
            RuntimeError,
            ValueError,
            TypeError,
        ) as exc:
            st.error(f"Inference failed: {exc}")

result = st.session_state.get("llm_result")

if result:
    st.subheader("Model response")
    st.write(result["response"])

    st.subheader("Run metrics")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Latency", f"{result['latency_ms']:.2f} ms")
    c2.metric("Input tokens", result["input_tokens"])
    c3.metric("Output tokens", result["output_tokens"])
    c4.metric("Total tokens", result["total_tokens"])

    st.caption(f"Model requested: {result['model']}")
    st.json(result)
