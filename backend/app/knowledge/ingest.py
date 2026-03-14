"""
Ingest knowledge into the RAG vector store. Run once after install to populate ChromaDB:
  cd backend && python -m app.knowledge.ingest

Sources: local markdown (hf_guidelines.md, medication_safety.md), OpenFDA/DailyMed drug
labels, PubMed abstracts, and local guideline files (PDF/txt/md in sources/guidelines).
See references.txt.
"""
from pathlib import Path
import re
import time

import httpx

from app.knowledge.rag import add_documents, clear_collection, KNOWLEDGE_DIR

# Heart-failure-relevant drugs for label ingestion (generic names)
HF_DRUGS = [
    "furosemide", "bumetanide", "torsemide",
    "lisinopril", "enalapril", "ramipril", "captopril",
    "carvedilol", "metoprolol", "bisoprolol",
    "spironolactone", "eplerenone",
    "empagliflozin", "dapagliflozin", "sotagliflozin",
    "digoxin", "sacubitril", "valsartan", "hydralazine", "isosorbide dinitrate",
]

# Key heart failure guideline and review PMIDs (abstracts ingested)
PUBMED_PMIDS = [
    "35363499",   # 2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure
    "35460242",   # Updated ACC/AHA/HFSA 2022 guidelines: what is new?
    "36460629",   # ACC/AHA/HFSA 2022 and ESC 2021 guidelines on heart failure comparison
    "34609399",   # 2021 ESC Guidelines for the diagnosis and treatment of acute and chronic HF
]

USER_AGENT = "DailyCare/1.0 (clinical knowledge ingestion; https://github.com/dailycare)"
REQUEST_TIMEOUT = 30.0


def _collect_local_docs() -> list[tuple[str, str]]:
    """Load curated markdown files."""
    docs = []
    for name, label in [("hf_guidelines", "Heart failure guidelines"), ("medication_safety", "Medication safety")]:
        path = KNOWLEDGE_DIR / f"{name}.md"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            docs.append((text, label))
    return docs


def _extract_openfda_label_sections(result: dict) -> str:
    """Build a single text from OpenFDA label JSON (one result)."""
    parts = []
    brand = (result.get("openfda") or {}).get("brand_name") or []
    generic = (result.get("openfda") or {}).get("generic_name") or []
    name = f"{', '.join(generic)} ({', '.join(brand)})" if brand else ", ".join(generic) or "Unknown"
    parts.append(f"# {name}\n")
    for key in ["indications_and_usage", "dosage_and_administration", "contraindications",
                "warnings", "adverse_reactions", "drug_interactions", "use_in_specific_populations"]:
        val = result.get(key)
        if isinstance(val, list) and val:
            val = val[0]
        if isinstance(val, str) and val.strip():
            title = key.replace("_", " ").title()
            parts.append(f"## {title}\n{val.strip()}\n")
    return "\n".join(parts).strip() or f"# {name}\n(No sections extracted)"


def fetch_openfda_labels() -> list[tuple[str, str]]:
    """Fetch drug labels from OpenFDA for HF-relevant drugs. Returns list of (text, source_label)."""
    docs = []
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        for drug in HF_DRUGS:
            try:
                r = client.get(
                    "https://api.fda.gov/drug/label.json",
                    params={"search": f'openfda.generic_name:"{drug}"', "limit": 1},
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                results = data.get("results") or []
                if not results:
                    continue
                text = _extract_openfda_label_sections(results[0])
                docs.append((text, f"OpenFDA/DailyMed: {drug}"))
            except Exception:
                continue
            time.sleep(0.4)  # be nice to the API
    return docs


def fetch_dailymed_labels() -> list[tuple[str, str]]:
    """Try DailyMed NLM API for SPL list by drug name; fetch one SPL per drug and extract text from XML."""
    docs = []
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        for drug in HF_DRUGS:
            try:
                r = client.get(
                    "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json",
                    params={"drug_name": drug, "pagesize": 1},
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                spls = data.get("data") or []
                if not spls:
                    continue
                set_id = spls[0].get("set_id")
                if not set_id:
                    continue
                r2 = client.get(
                    f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{set_id}.xml",
                )
                if r2.status_code != 200:
                    continue
                text = _extract_dailymed_spl_text(r2.text, drug)
                if text.strip():
                    docs.append((text, f"DailyMed: {drug}"))
            except Exception:
                continue
            time.sleep(0.5)
    return docs


def _extract_dailymed_spl_text(xml_text: str, drug: str) -> str:
    """Extract human-readable sections from DailyMed SPL XML (simplified)."""
    # SPL uses <section> with <title> and <text>. We strip tags and take first 20k chars.
    text_parts = re.findall(r"<text[^>]*>(.*?)</text>", xml_text, re.DOTALL | re.IGNORECASE)
    if not text_parts:
        # Fallback: remove all tags
        text = re.sub(r"<[^>]+>", " ", xml_text)
        text = re.sub(r"\s+", " ", text).strip()
        return f"# {drug}\n{text[:15000]}"
    combined = []
    for block in text_parts:
        clean = re.sub(r"<[^>]+>", " ", block)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean) > 100:
            combined.append(clean)
    return f"# DailyMed label: {drug}\n\n" + "\n\n".join(combined[:30])[:20000]


def fetch_pubmed_abstracts() -> list[tuple[str, str]]:
    """Fetch abstracts from PubMed for configured PMIDs. Returns list of (text, source_label)."""
    docs = []
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(PUBMED_PMIDS),
        "rettype": "abstract",
        "retmode": "text",
        "tool": "DailyCare",
        "email": "dailycare@example.com",
    }
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        try:
            r = client.get(base, params=params)
            if r.status_code != 200:
                return []
            # efetch retmode=text returns plain text with PMID and abstract per article
            text = r.text
            # Split by "PMID: " to get per-article blocks
            blocks = re.split(r"\n(?=PMID: \d+)", text)
            for block in blocks:
                block = block.strip()
                if not block:
                    continue
                m = re.search(r"PMID: (\d+)", block)
                pmid = m.group(1) if m else None
                if not pmid:
                    continue
                # First line often "PMID: 12345" and title; then abstract
                abstract_match = re.search(r"Abstract[:\s]*\n(.*)", block, re.DOTALL | re.IGNORECASE)
                body = abstract_match.group(1).strip() if abstract_match else block
                body = re.sub(r"\s+", " ", body).strip()[:8000]
                if body:
                    docs.append((f"# PubMed PMID {pmid}\n\n{body}", f"PubMed: PMID {pmid}"))
        except Exception:
            pass
    return docs


def _pdf_to_text(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        parts = []
        for i, page in enumerate(reader.pages):
            if i >= 100:
                break
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n\n".join(parts).strip() or ""
    except Exception:
        return ""


def ingest_guideline_files() -> list[tuple[str, str]]:
    """Load text from sources/guidelines: .md, .txt, and .pdf. Returns list of (text, source_label)."""
    docs = []
    guidelines_dir = KNOWLEDGE_DIR / "sources" / "guidelines"
    if not guidelines_dir.exists():
        return docs
    for path in guidelines_dir.iterdir():
        if path.is_dir():
            continue
        suf = path.suffix.lower()
        if suf == ".pdf":
            text = _pdf_to_text(path)
        elif suf in (".txt", ".md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
        else:
            continue
        if text.strip():
            docs.append((text.strip(), f"Guideline: {path.name}"))
    return docs


def run_full_ingest() -> None:
    """Clear RAG, then ingest from all sources and add_documents once."""
    all_docs: list[tuple[str, str]] = []

    local = _collect_local_docs()
    all_docs.extend(local)
    print(f"Local docs: {len(local)} file(s)")

    openfda = fetch_openfda_labels()
    if openfda:
        all_docs.extend(openfda)
        print(f"OpenFDA drug labels: {len(openfda)} drug(s)")
    else:
        dailymed = fetch_dailymed_labels()
        if dailymed:
            all_docs.extend(dailymed)
            print(f"DailyMed labels: {len(dailymed)} drug(s)")
        else:
            print("OpenFDA and DailyMed: skipped (API unavailable or rate limit)")

    pubmed = fetch_pubmed_abstracts()
    all_docs.extend(pubmed)
    print(f"PubMed abstracts: {len(pubmed)} article(s)")

    guidelines = ingest_guideline_files()
    all_docs.extend(guidelines)
    if guidelines:
        print(f"Guideline files: {len(guidelines)} file(s)")

    clear_collection()
    if all_docs:
        add_documents(all_docs)
        print(f"RAG store updated: {len(all_docs)} document(s) ingested.")
    else:
        print("No documents to ingest.")


if __name__ == "__main__":
    run_full_ingest()
