"""
Knowledge retriever: RAG over clinically validated sources when available,
with fallback to keyword-based static docs.
"""
from pathlib import Path


def _load_doc(name: str) -> str:
    path = Path(__file__).parent / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _get_context_fallback(query: str, max_chars: int) -> str:
    """Keyword-based inclusion from static markdown (used when RAG not populated)."""
    query_lower = query.lower()
    parts = []
    hf_text = _load_doc("hf_guidelines")
    med_text = _load_doc("medication_safety")
    hf_keywords = [
        "symptom", "lifestyle", "diet", "fluid", "salt", "weight", "stage", "nyha",
        "shortness", "breath", "swelling", "fatigue", "exercise", "smoking", "vaccin",
        "when to seek", "urgent", "heart failure",
    ]
    if any(k in query_lower for k in hf_keywords) or not query.strip():
        parts.append("## Heart failure guidelines\n" + hf_text)
    med_keywords = [
        "medication", "medicine", "pill", "adherence", "side effect", "contraindication",
        "ace", "arb", "beta", "diuretic", "potassium", "take", "dose", "frequency",
    ]
    if any(k in query_lower for k in med_keywords) or not query.strip():
        parts.append("## Medication safety\n" + med_text)
    if not parts:
        parts.append("## Heart failure guidelines\n" + hf_text)
        parts.append("## Medication safety\n" + med_text)
    combined = "\n\n".join(parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[Content truncated.]"
    return combined


def get_relevant_context(query: str, max_chars: int = 4000) -> str:
    """
    Return relevant medical knowledge for the query. Uses RAG (semantic search
    over embedded chunks) when the vector store is populated; otherwise falls
    back to keyword-based static docs. See references.txt for sources.
    """
    try:
        from app.knowledge.rag import query as rag_query, is_rag_available
        if is_rag_available():
            context = rag_query(query, max_chars=max_chars)
            if context:
                return context
    except Exception:
        pass
    return _get_context_fallback(query, max_chars)
