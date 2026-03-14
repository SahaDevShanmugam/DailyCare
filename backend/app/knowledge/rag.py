"""
RAG over clinically validated knowledge: embed chunks in ChromaDB, retrieve by semantic similarity.
Sources can be local docs (e.g. hf_guidelines.md, medication_safety.md) or ingested from
free external sources (DailyMed, guideline PDFs). See references.txt.
"""
from pathlib import Path
import re

# Lazy imports so backend starts without chromadb/sentence-transformers if not used
_collection = None
_embed_fn = None

KNOWLEDGE_DIR = Path(__file__).parent
CHROMA_DIR = KNOWLEDGE_DIR / "chroma_db"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 8
MAX_CHARS = 4000


def _get_embedding_model():
    global _embed_fn
    if _embed_fn is None:
        from sentence_transformers import SentenceTransformer
        _embed_fn = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_fn


def _get_client():
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection("dailycare_knowledge", metadata={"description": "HF and medication knowledge"})
    return _collection


def clear_collection() -> None:
    """Remove all documents from the RAG store (e.g. before full re-ingest)."""
    global _collection
    try:
        client = _get_client()
        client.delete_collection("dailycare_knowledge")
    except Exception:
        pass
    _collection = None


def _chunk_text(text: str, source: str) -> list[tuple[str, dict]]:
    """Split text into overlapping chunks. Prefer markdown section boundaries."""
    chunks = []
    # Split by ## or ### headers to keep sections together when possible
    sections = re.split(r"\n(?=##?\s)", text.strip())
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= CHUNK_SIZE:
            chunks.append((section, {"source": source}))
            continue
        # Break long sections by paragraphs or fixed size
        parts = re.split(r"\n\n+", section)
        current = ""
        for p in parts:
            if len(current) + len(p) + 2 <= CHUNK_SIZE:
                current += "\n\n" + p if current else p
            else:
                if current:
                    chunks.append((current.strip(), {"source": source}))
                if len(p) > CHUNK_SIZE:
                    for i in range(0, len(p), CHUNK_SIZE - CHUNK_OVERLAP):
                        chunk = p[i : i + CHUNK_SIZE]
                        if chunk.strip():
                            chunks.append((chunk.strip(), {"source": source}))
                    current = ""
                else:
                    current = p
        if current.strip():
            chunks.append((current.strip(), {"source": source}))
    return chunks


def add_documents(docs: list[tuple[str, str]]) -> None:
    """
    Ingest documents into the vector store. Each item is (text, source_label).
    """
    coll = _get_collection()
    model = _get_embedding_model()
    all_chunks = []
    for text, source in docs:
        all_chunks.extend(_chunk_text(text, source))
    if not all_chunks:
        return
    texts = [c[0] for c in all_chunks]
    metadatas = [c[1] for c in all_chunks]
    ids = [f"chunk_{i}" for i in range(len(texts))]
    embeddings = model.encode(texts).tolist()
    coll.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def query(query_text: str, top_k: int = TOP_K, max_chars: int = MAX_CHARS) -> str:
    """
    Retrieve the most relevant chunks for the query and return concatenated text.
    Returns empty string if collection is empty or query fails.
    """
    try:
        coll = _get_collection()
        if coll.count() == 0:
            return ""
        model = _get_embedding_model()
        q_emb = model.encode([query_text]).tolist()
        results = coll.query(query_embeddings=q_emb, n_results=min(top_k, coll.count()), include=["documents", "metadatas"])
        docs = results["documents"][0] if results["documents"] else []
        combined = "\n\n".join(docs).strip()
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "\n\n[Content truncated.]"
        return combined
    except Exception:
        return ""


def is_rag_available() -> bool:
    """True if ChromaDB has been populated (at least one chunk)."""
    try:
        coll = _get_collection()
        return coll.count() > 0
    except Exception:
        return False
