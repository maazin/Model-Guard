"""Local document chunking and TF-IDF retrieval (ADR-0006).

Only approved governance documents for the selected model version are indexed. Chunks are
section-level so every hit carries a (document_id, section) citation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from modelguard_governance.documents import parse_front_matter, sections


@dataclass(frozen=True)
class Chunk:
    document_id: str
    document_type: str
    section: str
    text: str


def chunk_document(document_id: str, document_type: str, content: str) -> list[Chunk]:
    _, body = parse_front_matter(content)
    out = []
    for heading, text in sections(body).items():
        # Title lines and boilerplate before the first heading are not citable evidence.
        if not text.strip() or not heading:
            continue
        out.append(Chunk(document_id, document_type, heading, text.strip()))
    return out


class LocalIndex:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self._vec: TfidfVectorizer | None = None
        self._matrix = None
        if chunks:
            self._vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
            corpus = [f"{c.document_type} {c.section} {c.text}" for c in chunks]
            self._matrix = self._vec.fit_transform(corpus)

    def search(self, query: str, k: int = 6) -> list[tuple[Chunk, float]]:
        if not self.chunks or self._vec is None or self._matrix is None:
            return []
        q = self._vec.transform([query])
        scores = np.asarray((self._matrix @ q.T).todense()).ravel()
        order = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in order if scores[i] > 0]
