# Astro Object Chat Assistant

## Table of Contents

1. [Short Description](#i-short-description)
2. [Tech Stack](#ii-tech-stack)
3. [Project Structure](#iii-project-structure)
4. [Getting Started](#iv-getting-started)
5. [Data and RAG Pipeline](#v-data-and-rag-pipeline)
6. [Using the Chat Assistant](#vi-using-the-chat-assistant)
7. [Deploying](#vii-deploying)
8. [FAQ](#viii-faq)
9. [Current Status and Scope](#ix-current-status-and-scope)

---

## I. Short Description

Astro Object Chat Assistant is a retrieval-augmented generation (RAG)
chatbot that answers questions about the 50 brightest named stars in a
curated subset of the [HYG stellar database](https://codeberg.org/astronexus/hyg).
It was built as a Hacktiv8 final project for the “LLM-Based Tools and Gemini
API Integration for Data Scientists” program.

The application combines a local Chroma vector store with Gemini embeddings
and Gemini generation. A Streamlit interface provides a conversational
experience, while the prompt intentionally limits answers to the retrieved
star records instead of allowing unsupported general-knowledge answers.

This is a self-contained prototype. It does not make live calls to SIMBAD,
NASA's Exoplanet Archive, or the separate
`astronomy-multi-catalog-identifier-matcher` FastAPI project.

## II. Tech Stack

| Layer | Choice | Purpose |
| --- | --- | --- |
| **Language** | Python | Application and data-ingestion code |
| **UI** | [Streamlit](https://streamlit.io/) | Chat interface and session history |
| **Orchestration** | [LangChain](https://www.langchain.com/) | Retrieval and generation pipeline |
| **Embeddings** | Gemini `gemini-embedding-001` | Converts star records and queries into vectors |
| **Vector store** | [Chroma](https://www.trychroma.com/) | Persists and searches the local embeddings |
| **Generation** | Gemini `gemini-3.6-flash` | Produces the final answer from retrieved context |
| **Data processing** | [pandas](https://pandas.pydata.org/) | Reads and processes the CSV dataset |
| **Configuration** | `python-dotenv` | Loads local environment variables from `.env` |

The vector store is created locally at `./chroma_db` and is ignored by Git.
It must be rebuilt in each environment after the dependencies and API key
are configured.

## III. Project Structure

```text
.
├── app.py                    # Streamlit chat UI
├── ingest.py                 # Builds the Chroma vector store from the CSV
├── rag_chain.py              # Retriever, prompt, Gemini model, and chain
├── requirements.txt          # Python dependencies
├── .env.example              # Environment-variable template
└── data/
    └── hyg_top50_named.csv   # Curated 50-star HYG subset
```

The generated `chroma_db/` directory is runtime data, not source code. It is
created by `ingest.py` and consumed by `rag_chain.py`.

## IV. Getting Started

### Prerequisites

- Python and `pip`
- A Gemini API key
- Internet access during ingestion and chat requests, because Gemini is used
  for embeddings and response generation

### Installation

From the repository root:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell, use this equivalent command:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder value with your key:

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
```

`rag_chain.py` and `ingest.py` also recognize `GOOGLE_API_KEY`. If only
`GEMINI_API_KEY` is set, the application mirrors it to `GOOGLE_API_KEY` for
the LangChain Google integration.

### Build the vector store

Run ingestion once before starting the UI:

```bash
python ingest.py
```

The script reads the CSV, creates one document per star, generates embeddings,
and persists the collection named `hyg_stars` in `./chroma_db`.

### Start the application

```bash
streamlit run app.py
```

Streamlit prints a local URL in the terminal. Open that URL in a browser to
use the chat assistant.

## V. Data and RAG Pipeline

### Source data

`data/hyg_top50_named.csv` is a curated subset of HYG containing the 50
brightest stars with a real proper name. The source includes identifiers,
coordinates, distance in parsecs, magnitudes, spectral class, constellation,
and related catalog fields.

The ingestion script converts distance from parsecs to light-years using
`1 parsec = 3.26156 light-years`. Each row becomes one document containing:

- Proper name and optional Bayer/Flamsteed designation
- Spectral class
- Approximate distance in light-years
- Constellation
- Apparent and absolute magnitude
- Optional hand-written notable facts for Betelgeuse, Sirius, Polaris, and
  Antares

### Retrieval and generation

For each question:

1. The question is embedded with `gemini-embedding-001`.
2. Chroma retrieves the four most similar star records.
3. The records and the recent conversation are inserted into the system
   prompt.
4. `gemini-3.6-flash` generates the answer.
5. The response is rendered in the Streamlit chat and saved to the current
   session.

The prompt instructs the assistant to say plainly when a star is outside the
dataset or when the retrieved records do not support an answer. Retrieval is
not a guarantee of factual completeness; it is the boundary used by this
prototype to reduce unsupported answers.

### Rebuilding after data changes

Run ingestion again after changing the CSV or the document template:

```bash
python ingest.py
```

If a stale local store needs to be replaced, stop the application, remove
the specific `chroma_db/` directory, and run ingestion again.

## VI. Using the Chat Assistant

The interface starts with an empty conversation. Example questions include:

- “How far away is Sirius?”
- “Compare Vega and Betelgeuse.”
- “What spectral class is Rigil Kentaurus?”
- “Tell me about the notable fact recorded for Polaris.”

The application keeps the current conversation in
`st.session_state["messages"]`. For follow-up questions, it sends the most
recent turns as plain-text chat history so questions such as “what about its
companion?” can use the preceding context.

The history is in-memory only. Refreshing the page or restarting Streamlit
starts a new conversation.

## VII. Deploying

The application can run on any host that supports Python, Streamlit, the
listed dependencies, and outbound requests to Gemini.

At deployment time:

1. Install the dependencies from `requirements.txt`.
2. Provide `GEMINI_API_KEY` as a platform secret or environment variable.
3. Run `python ingest.py` in the deployment environment to create the local
   Chroma store.
4. Start the service with `streamlit run app.py`.

Do not commit `.env`, API keys, or generated vector-store files. The provided
`.gitignore` excludes `.env` and common Python environment/build artifacts.
For hosts with ephemeral filesystems, ingestion must run during deployment or
as part of a startup step because `chroma_db/` is local persistent state.

## VIII. FAQ

### “Why does the app say it cannot load the vector store?”

Run `python ingest.py` first and confirm that `GEMINI_API_KEY` is set in the
environment. The app requires the generated `./chroma_db` directory and a
working Gemini configuration.

### “Can I ask about any astronomy topic?”

Not reliably. This prototype is designed for the 50 named stars represented
in the CSV. It should decline questions that cannot be answered from the
retrieved records rather than acting as a general astronomy search engine.

### “Why is a star not returned for a question?”

Retrieval is similarity-based and returns only four records. Use the star's
proper name in the question, then ask a focused follow-up if needed.

### “Why does a follow-up question work only during the current session?”

Conversation history is stored in Streamlit session state and is not written
to a database. A new browser session or page refresh does not retain it.

### “Why do I need to run ingestion again after deployment?”

Chroma is persisted in a local directory and is not checked into the
repository. A new machine or ephemeral deployment starts without the
generated embeddings, so the store must be built there.

## IX. Current Status and Scope

- **Implemented:** curated HYG top-50 dataset, one-document-per-star
  ingestion, Gemini embeddings, persisted Chroma retrieval, Gemini response
  generation, Streamlit chat UI, and short-term conversation context.
- **Intentionally out of scope:** authentication, multi-user storage,
  rate limiting, citations, live catalog queries, automatic dataset updates,
  and a general-purpose astronomy knowledge base.
- **Data limitation:** the answer quality and coverage are bounded by the
  records and notable-facts blurbs in `data/hyg_top50_named.csv` and
  `ingest.py`.
- **Prototype limitation:** API failures and model errors are shown in the
  Streamlit interface, but there is no production observability or retry
  system yet.

The project is suitable as a local demonstration of a focused RAG workflow:
curated data is transformed into documents, embedded into a local vector
store, retrieved per question, and passed to a constrained language-model
prompt.
