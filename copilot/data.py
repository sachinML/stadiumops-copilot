from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .rag import BM25Index, chunk_text, DocChunk


def load_pois(data_dir: str | Path) -> dict[str, Any]:
    p = Path(data_dir) / "pois.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, Any] = {}
    for poi in raw.get("pois", []):
        pid = str(poi.get("id") or poi.get("name") or "")
        if pid:
            out[pid] = poi
    return out


def load_kb(data_dir: str | Path) -> tuple[BM25Index, list[DocChunk]]:
    data_dir = Path(data_dir)
    kb_dir = data_dir / "knowledge"
    chunks: list[DocChunk] = []
    for path in sorted(kb_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("_", " ").title()
        chunks.extend(chunk_text(doc_id=path.stem, title=title, text=text))
    index = BM25Index(chunks)
    return index, chunks

