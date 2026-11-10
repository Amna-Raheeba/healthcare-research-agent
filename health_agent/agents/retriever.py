"""Retriever: BM25 over the corpus, with a stub interface for dense search.

BM25 is the default on purpose. It needs no embeddings service, it is
deterministic (same question -> same ranking, which matters when you are
debugging a wrong citation), and on a small curated corpus it is hard to
beat. ``VectorIndex`` below is the seam where a FAISS/Chroma index would
slot in for a larger corpus — it is an interface, not a fake
implementation pretending to do dense retrieval.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Protocol

from ..state import Plan, RetrievedChunk
from ..text_utils import content_tokens, stemmed_tokens, tokenize
from ..tools.corpus import Document


class BM25Index:
    def __init__(self, documents: list[Document], k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self._doc_tokens: list[list[str]] = [stemmed_tokens(d.searchable_text) for d in documents]
        self._doc_freq: Counter[str] = Counter()
        for tokens in self._doc_tokens:
            self._doc_freq.update(set(tokens))
        self._avg_len = sum(len(t) for t in self._doc_tokens) / max(len(self._doc_tokens), 1)
        self._n = len(documents)

    def _idf(self, term: str) -> float:
        df = self._doc_freq.get(term, 0)
        # Robertson-Walker IDF with +0.5 smoothing, floored at a small positive value.
        return max(math.log(1 + (self._n - df + 0.5) / (df + 0.5)), 1e-6)

    def search(self, query: str, top_k: int = 4) -> list[tuple[Document, float]]:
        query_terms = content_tokens(query) or tokenize(query)
        if not query_terms:
            return []
        scored: list[tuple[Document, float]] = []
        for idx, doc_tokens in enumerate(self._doc_tokens):
            freq = Counter(doc_tokens)
            doc_len = len(doc_tokens)
            score = 0.0
            for term in query_terms:
                tf = freq.get(term, 0)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_len)
                score += self._idf(term) * (tf * (self.k1 + 1)) / denom
            if score > 0:
                scored.append((self.documents[idx], score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]


class VectorIndex(Protocol):
    """Interface a FAISS or Chroma adapter must satisfy to replace BM25."""

    def search(self, query: str, top_k: int = 4) -> list[tuple[Document, float]]: ...


class UnavailableVectorIndex:
    """Honest stub: raises instead of silently returning BM25 results."""

    def search(self, query: str, top_k: int = 4) -> list[tuple[Document, float]]:
        raise NotImplementedError(
            "Dense retrieval is not wired up. Install the optional extra and "
            "provide an embeddings-backed VectorIndex, or use BM25Index (default)."
        )


def retrieve(plan: Plan, index: BM25Index, top_k_per_query: int = 4, max_chunks: int = 6) -> list[RetrievedChunk]:
    best: dict[str, RetrievedChunk] = {}
    for sub in plan.sub_queries:
        for doc, score in index.search(sub.text, top_k=top_k_per_query):
            existing = best.get(doc.doc_id)
            if existing is None or score > existing.score:
                best[doc.doc_id] = RetrievedChunk(
                    doc_id=doc.doc_id, title=doc.title, source=doc.source, year=doc.year,
                    text=doc.text, score=round(float(score), 4), matched_query=sub.text,
                )
    ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)[:max_chunks]
    if len(ranked) > 2:
        # Relative relevance cutoff: on a focused question the best document
        # often scores several times higher than generic matches that share
        # words like "screening" or "adults". Keeping those weak chunks is
        # how off-topic citations end up in an answer, so drop chunks below
        # 30% of the top score. The top chunk is always kept.
        cutoff = ranked[0].score * 0.30
        ranked = ranked[:1] + [c for c in ranked[1:] if c.score >= cutoff]
    return ranked
