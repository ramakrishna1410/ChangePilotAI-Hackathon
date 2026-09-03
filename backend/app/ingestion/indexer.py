"""Embeds chunks and indexes them into Chroma (local stand-in for Azure AI
Search, §6.3). Metadata (repo/path/symbol/type) is stored alongside each
vector so retrieval can filter and the UI can show evidence.
"""
from __future__ import annotations

import chromadb
from openai import OpenAI

from app.config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, OPENAI_API_KEY
from app.ingestion.chunker import Chunk

_client = chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection():
    return _client.get_or_create_collection(name=CHROMA_COLLECTION)


def _embed(texts: list[str]) -> list[list[float]]:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def index_chunks(chunks: list[Chunk], batch_size: int = 50) -> int:
    collection = get_collection()
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embeddings = _embed([c.text for c in batch])
        collection.upsert(
            ids=[c.chunk_id for c in batch],
            embeddings=embeddings,
            documents=[c.text for c in batch],
            metadatas=[
                {
                    "source_path": c.source_path,
                    "symbol": c.symbol,
                    "chunk_type": c.chunk_type,
                    "language": c.language,
                    **c.metadata,
                }
                for c in batch
            ],
        )
        total += len(batch)
    return total


def reset_index() -> None:
    try:
        _client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass
