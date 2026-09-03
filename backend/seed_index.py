"""One-shot script: chunk + embed sample-app/ (or any target repo) into Chroma.

Usage: python seed_index.py [path-to-repo]
"""
import sys

from app.config import SAMPLE_APP_PATH
from app.ingestion.chunker import chunk_repository
from app.ingestion.indexer import index_chunks, reset_index


def main() -> None:
    repo_path = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_APP_PATH
    print(f"Chunking repository at {repo_path} ...")
    chunks = chunk_repository(repo_path)
    print(f"Produced {len(chunks)} semantic chunks.")

    reset_index()
    count = index_chunks(chunks)
    print(f"Indexed {count} chunks into Chroma collection.")

    by_type: dict[str, int] = {}
    for c in chunks:
        by_type[c.chunk_type] = by_type.get(c.chunk_type, 0) + 1
    for chunk_type, n in sorted(by_type.items()):
        print(f"  {chunk_type}: {n}")


if __name__ == "__main__":
    main()
