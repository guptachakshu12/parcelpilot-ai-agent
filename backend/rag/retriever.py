from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAG_DIR = PROJECT_ROOT / "backend" / "rag"

INDEX_FILE = RAG_DIR / "parcelpilot.index"
METADATA_FILE = RAG_DIR / "metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"


# Load the saved FAISS index
if not INDEX_FILE.exists():
    raise FileNotFoundError(
        f"FAISS index not found: {INDEX_FILE}"
    )

index = faiss.read_index(str(INDEX_FILE))


# Load chunk metadata
if not METADATA_FILE.exists():
    raise FileNotFoundError(
        f"Metadata file not found: {METADATA_FILE}"
    )

with open(METADATA_FILE, "r", encoding="utf-8") as file:
    metadata = json.load(file)


# Load the same embedding model used during ingestion
model = SentenceTransformer(MODEL_NAME)


def search_documents(query: str, top_k: int = 3):
    """
    Search the ParcelPilot document collection.

    Returns the most relevant document chunks.
    """

    if not query or not query.strip():
        return []

    # Convert query into an embedding
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    # Normalize because the FAISS index uses cosine-style similarity
    faiss.normalize_L2(query_embedding)

    # Search FAISS
    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):

        # -1 means FAISS did not find a result
        if idx == -1:
            continue

        document = metadata[idx]

        results.append({
            "score": float(score),
            "source": document["source"],
            "page": document["page"],
            "text": document["text"]
        })

    return results


if __name__ == "__main__":

    print("\n========== TESTING DOCUMENT SEARCH ==========\n")

    test_queries = [
        "What is Northstar's cancellation policy?",
        "What is the service credit policy?",
        "What is the current P1 response target?",
        "Why can SwiftShip shipments still show BOOKED after pickup?"
    ]

    for query in test_queries:

        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        results = search_documents(query, top_k=3)

        for i, result in enumerate(results, start=1):

            print(f"\nResult {i}")
            print(f"Score: {result['score']:.4f}")
            print(f"Source: {result['source']}")
            print(f"Page: {result['page']}")
            print(f"Text: {result['text'][:500]}")