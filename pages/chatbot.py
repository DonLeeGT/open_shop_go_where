import streamlit as st
from rag import ask

st.title("Open Shop Go Where?")
with st.expander("DISCLAIMER"):
    st.write(
        "This web application is a prototype developed for educational purposes only. "
        "The information provided here is NOT intended for real-world usage and should not be "
        "relied upon for making any decisions, especially those related to financial, legal, or "
        "healthcare matters.\n\n"
        "Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. "
        "You assume full responsibility for how you use any generated output.\n\n"
        "Always consult with qualified professionals for accurate and personalised advice."
    )
st.caption("Ask me anything about HDB commercial property listings, tenancy terms, e-bidding, and more.")

vector_store = st.session_state.get("vector_store")
units = st.session_state.get("place2lease_units", [])
if not vector_store:
    st.error("RAG pipeline not initialized. Please reload the app.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. I want to open a cafe in the west."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            answer, retrieved = ask(vector_store, prompt, units=units)
        st.markdown(answer)

        with st.expander("Sources"):
            for i, doc in enumerate(retrieved, 1):
                source = doc.metadata.get("source", "unknown")
                st.markdown(f"**[{i}] {source}**")
                st.text(doc.page_content[:300])

    st.session_state["messages"].append({"role": "assistant", "content": answer})
