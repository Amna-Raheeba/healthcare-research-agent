"""Verifier: check every draft claim against the chunks it cites.

This is the step most RAG demos skip, and the reason this project exists.
A fluent answer can cite a real paper for a claim the paper never made.
Here, a claim survives only if a meaningful share of its content words
— and any numbers it states — actually appear in its cited chunk.

The check is lexical, not semantic, and the README says so. It catches
fabricated thresholds and invented statistics reliably; it will miss a
claim that reuses the right words with the wrong meaning. That trade-off
is documented, not hidden.
"""
from __future__ import annotations

import re

from ..state import Claim, RetrievedChunk, VerifiedClaim
from ..text_utils import overlap_ratio, split_sentences

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?")


def extract_claims(chunks: list[RetrievedChunk]) -> list[Claim]:
    """Draft claims are sentences taken from chunks, keeping their source index."""
    claims: list[Claim] = []
    for idx, chunk in enumerate(chunks, start=1):
        for sentence in split_sentences(chunk.text):
            claims.append(Claim(text=sentence, citation_index=idx))
    return claims


def _numbers_supported(claim_text: str, evidence: str) -> bool:
    numbers = _NUMBER_RE.findall(claim_text)
    return all(n in evidence for n in numbers)


def verify_claim(claim: Claim, chunks: list[RetrievedChunk], min_support_ratio: float = 0.32) -> VerifiedClaim:
    if claim.citation_index is None or not (1 <= claim.citation_index <= len(chunks)):
        return VerifiedClaim(claim, False, 0.0, None, "claim has no valid citation")
    chunk = chunks[claim.citation_index - 1]
    ratio = overlap_ratio(claim.text, chunk.text)
    if not _numbers_supported(claim.text, chunk.text):
        return VerifiedClaim(claim, False, ratio, chunk.doc_id, "a number in the claim does not appear in the cited source")
    if ratio < min_support_ratio:
        return VerifiedClaim(claim, False, ratio, chunk.doc_id, f"support ratio {ratio:.2f} below threshold {min_support_ratio:.2f}")
    return VerifiedClaim(claim, True, ratio, chunk.doc_id, "supported by cited chunk")


def verify_claims(claims: list[Claim], chunks: list[RetrievedChunk], min_support_ratio: float = 0.32) -> list[VerifiedClaim]:
    return [verify_claim(c, chunks, min_support_ratio) for c in claims]
