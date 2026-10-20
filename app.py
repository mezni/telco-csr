import streamlit as st

from telco_csr.nodes.intent_router import intent_router_node

st.set_page_config(
    page_title="Node A: Intent Router Playground", page_icon="🧭", layout="centered"
)

st.title("🧭 Node A: Intent Router Playground")
st.caption("Isolated test environment for telecom operational intent classification.")

# Sidebar Configuration for Threshold Settings
with st.sidebar:
    st.header("⚙️ Router Settings")
    confidence_threshold = st.slider(
        "Fallback Confidence Threshold", 0.0, 1.0, 0.70, 0.05
    )
    st.info(
        "Queries falling below this threshold automatically route "
        "to `GENERAL_FAQ` / fallback."
    )

# User Input Form
with st.form("intent_form"):
    user_query = st.text_area(
        "Enter Customer Query:",
        placeholder="e.g., Why is my data roaming charge so high this month?",
        height=100,
    )
    submitted = st.form_submit_button("Classify Intent", type="primary")

if submitted:
    if not user_query.strip():
        st.warning("Please enter a valid customer query.")
    else:
        with st.spinner("Analyzing intent with LLM..."):
            try:
                state = {"latest_user_message": user_query}

                # Execute Node A
                result = intent_router_node(state)

                intent = result["current_intent"]
                confidence = result["router_confidence"]
                reasoning = result["router_reasoning"]

                # Display Results
                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    st.metric(label="Detected Intent", value=intent)
                with col2:
                    st.metric(
                        label="Confidence Score", value=f"{confidence * 100:.1f}%"
                    )

                if confidence < confidence_threshold:
                    st.warning(
                        f"⚠️ Confidence score ({confidence:.2f}) is below "
                        f"threshold ({confidence_threshold}). "
                        "Triggered fallback route."
                    )

                st.markdown("**LLM Reasoning:**")
                st.info(reasoning)

                with st.expander("🔍 Inspect Full State Payload"):
                    st.json(result)

            except Exception as e:
                st.error(
                    "Failed to execute intent classifier. Ensure your "
                    "`OPENAI_API_KEY` is configured in your `.env` file.\n\n"
                    f"Error: {e}"
                )
