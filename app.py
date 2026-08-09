"""
app.py

Streamlit chat UI for the Astro Object Chat Assistant. Run with:
    streamlit run app.py

Requires ./chroma_db to already exist — run ingest.py first.
"""

import streamlit as st
from dotenv import load_dotenv
from rag_chain import build_chain

load_dotenv()

st.set_page_config(page_title="Astro Object Chat Assistant", page_icon="\u2728")
st.title("\u2728 Astro Object Chat Assistant")
st.caption(
    "Ask me about any of the 50 brightest named stars — e.g. Sirius, "
    "Betelgeuse, Vega, Rigil Kentaurus. I only know what's in my dataset."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chain" not in st.session_state:
    try:
        st.session_state.chain = build_chain()
    except Exception as e:
        st.error(
            "Couldn't load the vector store or model. Have you run "
            f"`python ingest.py` and set GEMINI_API_KEY in .env?\n\nDetails: {e}"
        )
        st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask about a star..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # last few turns as simple text, so follow-ups like "what about its
    # companion?" can resolve against prior context
    history_turns = st.session_state.messages[-9:-1]
    chat_history = "\n".join(
        f"{t['role']}: {t['content']}" for t in history_turns
    ) or "(no prior turns)"

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chain.invoke(
                {"question": question, "chat_history": chat_history}
            )
        except Exception as e:
            response = f"Something went wrong generating a response: {e}"
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
