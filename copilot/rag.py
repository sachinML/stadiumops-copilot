from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable


_WORD_RE = re.compile(r"[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?")


def _tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


@dataclass(frozen=True)
class DocChunk:
    doc_id: str
    title: str
    text: str


class BM25Index:
    def __init__(self, chunks: list[DocChunk]):
        self._chunks = chunks
        self._chunk_tokens = [_tokenize(c.text) for c in chunks]
        self._avgdl = (sum(len(t) for t in self._chunk_tokens) / max(1, len(self._chunk_tokens))) or 1.0
        self._df: dict[str, int] = {}
        for toks in self._chunk_tokens:
            for w in set(toks):
                self._df[w] = self._df.get(w, 0) + 1

    def search(self, query: str, *, k: int = 4) -> list[tuple[DocChunk, float]]:
        q = _tokenize(query)
        if not q:
            return []

        N = max(1, len(self._chunks))
        k1 = 1.2
        b = 0.75

        scores: list[tuple[int, float]] = []
        for i, toks in enumerate(self._chunk_tokens):
            if not toks:
                continue
            tf: dict[str, int] = {}
            for w in toks:
                tf[w] = tf.get(w, 0) + 1
            dl = len(toks)
            score = 0.0
            for w in q:
                f = tf.get(w, 0)
                if f == 0:
                    continue
                df = self._df.get(w, 0)
                idf = math.log(1.0 + (N - df + 0.5) / (df + 0.5))
                denom = f + k1 * (1.0 - b + b * (dl / self._avgdl))
                score += idf * (f * (k1 + 1.0) / denom)
            if score > 0:
                scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self._chunks[i], s) for i, s in scores[:k]]


def chunk_text(doc_id: str, title: str, text: str, *, max_chars: int = 900) -> list[DocChunk]:
    parts: list[str] = []
    buf: list[str] = []
    cur = 0
    for line in text.splitlines():
        add = len(line) + 1
        if cur + add > max_chars and buf:
            parts.append("\n".join(buf).strip())
            buf = []
            cur = 0
        buf.append(line)
        cur += add
    if buf:
        parts.append("\n".join(buf).strip())
    out: list[DocChunk] = []
    for idx, p in enumerate(parts):
        if p:
            out.append(DocChunk(doc_id=f"{doc_id}#{idx+1}", title=title, text=p))
    return out


def format_retrieved(chunks: Iterable[DocChunk]) -> str:
    blocks = []
    for c in chunks:
        blocks.append(f"[{c.doc_id}] {c.title}\n{c.text}".strip())
    return "\n\n---\n\n".join(blocks)

