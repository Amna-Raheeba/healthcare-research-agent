"""Small text helpers shared by planner, retriever, verifier and answerer."""
from __future__ import annotations

import re

STOPWORDS = frozenset(
    """a an the and or of for to in on at by with from as is are was were be been being
    do does did what which who whom when where why how can could should would may might
    i you he she it we they this that these those there here about into than then so such
    if but not no yes have has had will shall per""".split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def stem(token: str) -> str:
    """Crude suffix stripping so 'screening'/'screened'/'screens' match.

    Not a Porter stemmer — just enough normalisation for lexical matching
    in a small corpus, and easy to reason about.
    """
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def stemmed_tokens(text: str) -> list[str]:
    return [stem(t) for t in tokenize(text)]


def content_tokens(text: str) -> list[str]:
    return [stem(t) for t in tokenize(text) if t not in STOPWORDS and len(t) > 1]


def split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_RE.split(text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 20]


def overlap_ratio(claim: str, evidence: str) -> float:
    """Fraction of distinct claim content tokens present in evidence."""
    claim_tokens = set(content_tokens(claim))
    if not claim_tokens:
        return 0.0
    evidence_tokens = set(stemmed_tokens(evidence))
    return len(claim_tokens & evidence_tokens) / len(claim_tokens)
