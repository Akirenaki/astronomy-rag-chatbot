"""
ingest.py

Reads the curated HYG star subset (data/hyg_top50_named.csv), turns each row
into one templated text document (one star = one document, no text-splitting
needed), embeds each document with Gemini's gemini-embedding-001 model, and
persists the result to a local Chroma vector store at ./chroma_db.

Run this once before starting the Streamlit app, and again any time the
dataset or template changes.

Usage:
    python ingest.py
"""

import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DATA_PATH = "data/hyg_top50_named.csv"
PERSIST_DIR = "./chroma_db"
PARSEC_TO_LY = 3.26156

# Optional hand-written notable-facts blurbs, keyed by proper name.
# Add to this dict for any of the 50 stars you want to enrich further.
NOTABLE_FACTS = {
    "Betelgeuse": "It is a variable red supergiant nearing the end of its "
                  "life and is expected to eventually explode as a supernova.",
    "Sirius": "It is actually a binary system: the bright star seen with "
              "the naked eye has a faint white dwarf companion, Sirius B.",
    "Polaris": "Although not the brightest star in the sky, it sits almost "
               "exactly above Earth's north celestial pole, making it the "
               "current north star.",
    "Antares": "Its name means 'rival of Mars' because its red color and "
               "brightness are often confused with the planet Mars.",
}


def build_document(row: pd.Series) -> Document:
    """Turn one HYG row into a single templated Document."""
    distance_ly = row["dist"] * PARSEC_TO_LY

    designation = row["bf"] if isinstance(row["bf"], str) and row["bf"].strip() else None
    designation_part = f" ({designation})" if designation else ""

    text = (
        f"{row['proper']}{designation_part} is a {row['spect']} star "
        f"located approximately {distance_ly:.1f} light-years away, "
        f"in the constellation {row['con']}. "
        f"It has an apparent magnitude of {row['mag']} and an absolute "
        f"magnitude of {row['absmag']}."
    )

    blurb = NOTABLE_FACTS.get(row["proper"])
    if blurb:
        text += f" {blurb}"

    return Document(
        page_content=text,
        metadata={
            "proper_name": row["proper"],
            "constellation": row["con"],
            "spectral_class": row["spect"],
            "distance_ly": round(distance_ly, 2),
            "apparent_magnitude": row["mag"],
        },
    )


def main():
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY not set. Copy .env.example to .env and add your key."
        )
    # langchain-google-genai reads GOOGLE_API_KEY; mirror it if only
    # GEMINI_API_KEY was provided.
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} stars from {DATA_PATH}")

    docs = [build_document(row) for _, row in df.iterrows()]
    print(f"Built {len(docs)} documents. Example:\n{docs[0].page_content}\n")

    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

    print(f"Embedding and persisting to {PERSIST_DIR} ...")
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name="hyg_stars",
    )
    print("Done. Vector store ready.")


if __name__ == "__main__":
    main()
