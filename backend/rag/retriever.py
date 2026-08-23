from pathlib import Path
import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# RAG files
RAG_DIR = PROJECT_ROOT / "backend" / "rag"
INDEX_FILE = RAG_DIR / "parcelpilot.index"
METADATA_FILE = RAG_DIR / "metadata.json"

# Gemini embedding model
EMBEDDING_MODEL = "gemini-embedding-001"

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def create_embedding(text):
    """Create a Gemini embedding for a query."""

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )

    embedding = np.array(
        [response.embeddings[0].values],
        dtype="float32"
    )

    # Same normalization used during ingestion
    faiss.normalize_L2(embedding)

    return embedding


def load_rag_data():
    """Load FAISS index and document metadata."""

    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {INDEX_FILE}"
        )

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_FILE}"
        )

    index = faiss.read_index(
        str(INDEX_FILE)
    )

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        metadata = json.load(file)

    return index, metadata


def search_documents(query, top_k=5):
    """Search the FAISS index using Gemini embeddings."""

    index, metadata = load_rag_data()

    query_embedding = create_embedding(query)

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, index_id in zip(
        scores[0],
        indices[0]
    ):
        if index_id == -1:
            continue

        document = metadata[index_id].copy()

        document["score"] = float(score)

        results.append(document)

    return results


if __name__ == "__main__":
    query = "Is LumenWorks eligible for a service credit?"

    results = search_documents(query)

    for result in results:
        print("\n--------------------")
        print(f"Score: {result['score']}")
        print(f"Source: {result['source']}")
        print(f"Page: {result['page']}")
        print(result["text"])