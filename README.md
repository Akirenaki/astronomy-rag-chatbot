# Astro Object Chat Assistant

A RAG chatbot that answers questions about the 50 brightest named stars,
built for the Hacktiv8 "LLM-Based Tools and Gemini API Integration for Data
Scientists" final project.

Framed as a small, decoupled prototype/precursor to a future conversational
layer on `astronomy-multi-catalog-identifier-matcher` (a separate FastAPI
project). This app makes no live calls to that project or to SIMBAD/NASA
Exoplanet Archive — it runs entirely against a static, curated subset of the
[HYG stellar database](https://codeberg.org/astronexus/hyg) (CC BY-SA 4.0).

## Stack

- **Data:** HYG database (Hipparcos + Yale Bright Star + Gliese), filtered to
  the 50 brightest stars with a real proper name
- **Embeddings:** Gemini `gemini-embedding-001`
- **Vector store:** Chroma (persisted locally at `./chroma_db`)
- **Generation:** Gemini `gemini-3.6-flash` via `langchain-google-genai`
- **UI:** Streamlit, with chat history kept in `st.session_state`

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your real GEMINI_API_KEY
```

## Run

```bash
# 1. Build the vector store (only needed once, or after changing the dataset)
python ingest.py

# 2. Launch the chat UI
streamlit run app.py
```

In GitHub Codespaces, Streamlit's forwarded port will open automatically in
the browser preview panel.

## Files

| File | Purpose |
|---|---|
| `data/hyg_top50_named.csv` | The curated 50-star subset of HYG used as the knowledge base |
| `ingest.py` | One-off script: CSV rows → templated documents → Gemini embeddings → Chroma |
| `rag_chain.py` | Builds the retrieval + generation chain (retriever, prompt, LLM) |
| `app.py` | Streamlit chat UI; imports the chain from `rag_chain.py` |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for required environment variables (safe to commit) |

## Notes

- The assistant only answers from the retrieved star records and will say so
  plainly if asked about a star outside the 50-star dataset.
- No auth, no multi-user rate limiting, no live catalog calls — intentionally
  out of scope for this build.
