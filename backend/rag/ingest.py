from pathlib import Path
import json
import os

import faiss
from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Folder containing assessment PDFs
DATA_DIR = PROJECT_ROOT / "data"

# RAG output
RAG_DIR = PROJECT_ROOT / "backend" / "rag"
INDEX_FILE = RAG_DIR / "parcelpilot.index"
METADATA_FILE = RAG_DIR / "metadata.json"

# Gemini embedding model
EMBEDDING_MODEL = "gemini-embedding-001"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_pdf_text(pdf_path):
    """Extract text from every page of a PDF."""

    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text() or ""

        if text.strip():
            pages.append({
                "page": page_number + 1,
                "text": text
            })

    return pages


def create_chunks(text, chunk_size=800, overlap=150):
    """Split text into overlapping chunks."""

    text = " ".join(text.split())

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def create_embeddings(texts):
    """Create Gemini embeddings."""

    embeddings = []

    for i, text in enumerate(texts):
        print(f"Embedding {i + 1}/{len(texts)}")

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )

        embeddings.append(response.embeddings[0].values)

    return embeddings


def ingest_documents():
    """Read PDFs, create Gemini embeddings and build FAISS index."""

    pdf_files = sorted(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {DATA_DIR}"
        )

    print(f"Found {len(pdf_files)} PDF files.")

    documents = []

    for pdf_path in pdf_files:

        print(f"\nProcessing: {pdf_path.name}")

        pages = extract_pdf_text(pdf_path)

        print(f"Pages with text: {len(pages)}")

        for page_data in pages:

            chunks = create_chunks(page_data["text"])

            for chunk in chunks:

                documents.append({
                    "text": chunk,
                    "source": pdf_path.name,
                    "page": page_data["page"]
                })

    print(f"\nTotal chunks created: {len(documents)}")

    if not documents:
        raise ValueError(
            "No text could be extracted from the PDFs."
        )

    texts = [doc["text"] for doc in documents]

    print("\nCreating Gemini embeddings...")

    embeddings = create_embeddings(texts)

    # Convert to numpy float32
    import numpy as np

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    print(f"Embedding dimension: {dimension}")

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    # Create RAG directory
    RAG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save FAISS index
    faiss.write_index(
        index,
        str(INDEX_FILE)
    )

    # Save metadata
    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n========== RAG INGESTION COMPLETE ==========")
    print(f"Documents: {len(pdf_files)}")
    print(f"Chunks: {len(documents)}")
    print(f"FAISS index: {INDEX_FILE}")
    print(f"Metadata: {METADATA_FILE}")


if __name__ == "__main__":
    ingest_documents()