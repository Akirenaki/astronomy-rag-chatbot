"""
rag_chain.py

Builds the retrieval-augmented generation chain: Chroma retriever (top-k
similarity search) feeding retrieved star records + recent chat history into
Gemini 3.6 Flash for generation. Imported by app.py; not meant to be run
directly.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

PERSIST_DIR = "./chroma_db"
K = 4  # number of retrieved star records per query

SYSTEM_PROMPT = """You are a friendly, precise astronomy tutor. Answer using \
only the retrieved star record(s) provided below. If a question is about a \
star outside this dataset, or can't be answered from the retrieved records, \
say so plainly rather than guessing or drawing on outside knowledge. When \
useful, mention which star record(s) your answer is based on. Keep the tone \
approachable for an undergraduate-level audience, but don't sacrifice \
precision on numbers such as distance, magnitude, and spectral class.

Retrieved star record(s):
{context}

Recent conversation:
{chat_history}"""


def format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


def get_retriever():
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
        collection_name="hyg_stars",
    )
    return vectorstore.as_retriever(search_kwargs={"k": K})


def build_chain():
    """Returns a callable chain: invoke({"question": ..., "chat_history": ...})."""
    retriever = get_retriever()
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )

    chain = (
        {
            "context": (lambda x: x["question"]) | retriever | format_docs,
            "chat_history": lambda x: x["chat_history"],
            "question": lambda x: x["question"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain
