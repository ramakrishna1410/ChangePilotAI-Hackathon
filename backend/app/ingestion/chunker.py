"""Semantic chunking for the .NET codebase (§6.2): prefer class/method/stored
procedure/doc-section units over fixed-size text windows, and attach source
metadata so the UI can show evidence and agents can cite it.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chunk:
    chunk_id: str
    source_path: str
    symbol: str
    chunk_type: str  # class | method | sql_procedure | doc_section
    language: str
    text: str
    metadata: dict = field(default_factory=dict)


def _make_id(source_path: str, symbol: str) -> str:
    digest = hashlib.sha1(f"{source_path}::{symbol}".encode()).hexdigest()[:10]
    return f"{Path(source_path).stem}-{symbol}-{digest}".replace(" ", "_")


_CS_TYPE_RE = re.compile(r"\b(class|interface|enum)\s+(\w+)")
_CS_METHOD_RE = re.compile(
    r"^\s*(?:public|private|protected|internal)\s+[\w<>,\[\]?\. ]+?\s+(\w+)\s*\([^;{]*\)\s*\{",
    re.MULTILINE,
)


def chunk_csharp_file(path: Path, root: Path) -> list[Chunk]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = str(path.relative_to(root))
    chunks: list[Chunk] = []

    type_match = _CS_TYPE_RE.search(text)
    class_name = type_match.group(2) if type_match else path.stem

    # One chunk for the whole file header/using/namespace context (helps retrieval
    # find the class even when the query doesn't match a specific method body).
    chunks.append(
        Chunk(
            chunk_id=_make_id(rel, class_name),
            source_path=rel,
            symbol=class_name,
            chunk_type="class",
            language="csharp",
            text=text[:4000],
            metadata={"application": "SanofiOrders"},
        )
    )

    # Method-level chunks: find each method signature and grab its body via brace matching.
    for m in _CS_METHOD_RE.finditer(text):
        method_name = m.group(1)
        start = m.start()
        brace_start = text.index("{", start)
        depth = 0
        end = brace_start
        for i in range(brace_start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        method_text = text[start:end]
        symbol = f"{class_name}.{method_name}"
        chunks.append(
            Chunk(
                chunk_id=_make_id(rel, symbol),
                source_path=rel,
                symbol=symbol,
                chunk_type="method",
                language="csharp",
                text=method_text,
                metadata={"application": "SanofiOrders", "class": class_name},
            )
        )
    return chunks


_SQL_PROC_RE = re.compile(
    r"CREATE\s+PROCEDURE\s+([\w\.\[\]]+).*?(?=\nGO|\Z)", re.IGNORECASE | re.DOTALL
)


def chunk_sql_file(path: Path, root: Path) -> list[Chunk]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = str(path.relative_to(root))
    chunks = []
    for m in _SQL_PROC_RE.finditer(text):
        proc_name = m.group(1).strip()
        chunks.append(
            Chunk(
                chunk_id=_make_id(rel, proc_name),
                source_path=rel,
                symbol=proc_name,
                chunk_type="sql_procedure",
                language="sql",
                text=m.group(0).strip(),
                metadata={"application": "SanofiOrders"},
            )
        )
    return chunks


def chunk_markdown_file(path: Path, root: Path) -> list[Chunk]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = str(path.relative_to(root))
    sections = re.split(r"(?m)^(#{1,3} .+)$", text)
    chunks = []
    # sections alternates [preamble, heading, body, heading, body, ...]
    if sections and sections[0].strip():
        chunks.append(
            Chunk(
                chunk_id=_make_id(rel, "preamble"),
                source_path=rel,
                symbol=path.stem,
                chunk_type="doc_section",
                language="markdown",
                text=sections[0].strip(),
                metadata={"application": "SanofiOrders"},
            )
        )
    for i in range(1, len(sections), 2):
        heading = sections[i].strip("# ").strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""
        chunks.append(
            Chunk(
                chunk_id=_make_id(rel, heading),
                source_path=rel,
                symbol=heading,
                chunk_type="doc_section",
                language="markdown",
                text=f"{sections[i]}\n{body}".strip(),
                metadata={"application": "SanofiOrders"},
            )
        )
    return chunks


def chunk_repository(root: str | Path) -> list[Chunk]:
    root = Path(root)
    chunks: list[Chunk] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".cs":
            chunks.extend(chunk_csharp_file(path, root))
        elif path.suffix == ".sql":
            chunks.extend(chunk_sql_file(path, root))
        elif path.suffix == ".md":
            chunks.extend(chunk_markdown_file(path, root))
    return chunks
