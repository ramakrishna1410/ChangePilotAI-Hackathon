"""Hybrid retrieval (§6.3): vector similarity + keyword overlap, re-ranked
before being handed to the LLM as evidence. Retrieved text is always treated
as inert application data, never as instructions to the model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import RETRIEVAL_CANDIDATE_POOL, RETRIEVAL_TOP_K
from app.ingestion.indexer import _embed, get_collection

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")


@dataclass
class RetrievedChunk:
    chunk_id: str
    source_path: str
    symbol: str
    chunk_type: str
    text: str
    score: float


def _keyword_overlap(query_terms: set[str], text: str) -> int:
    text_terms = set(t.lower() for t in _WORD_RE.findall(text))
    return len(query_terms & text_terms)


def retrieve(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[RetrievedChunk]:
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_embedding = _embed([query])[0]
    n_results = min(RETRIEVAL_CANDIDATE_POOL, collection.count())
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    query_terms = set(t.lower() for t in _WORD_RE.findall(query))
    candidates: list[RetrievedChunk] = []
    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for cid, doc, meta, dist in zip(ids, docs, metas, distances):
        vector_score = 1.0 - dist  # cosine distance -> similarity
        keyword_score = _keyword_overlap(query_terms, doc) / max(len(query_terms), 1)
        combined = (0.7 * vector_score) + (0.3 * keyword_score)
        candidates.append(
            RetrievedChunk(
                chunk_id=cid,
                source_path=meta.get("source_path", ""),
                symbol=meta.get("symbol", ""),
                chunk_type=meta.get("chunk_type", ""),
                text=doc,
                score=combined,
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:top_k]


def format_evidence_block(chunks: list[RetrievedChunk]) -> str:
    """Formats retrieved chunks as clearly-delimited, inert reference data."""
    parts = []
    for c in chunks:
        parts.append(
            f"--- EVIDENCE chunk_id={c.chunk_id} source={c.source_path} symbol={c.symbol} type={c.chunk_type} ---\n"
            f"{c.text}\n"
        )
    return "\n".join(parts)
