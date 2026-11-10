"""Answer composer: build the final answer *only* from verified claims.

Nothing reaches the user that the verifier rejected. Sentences are
ranked by how much of the *question* they cover (not the other way round
— a long evidence sentence will always contain many words the question
never mentioned), weighted by how strongly their source was retrieved,
deduplicated, and capped so the answer stays readable.
"""
from __future__ import annotations

from ..guardrails import DISCLAIMER
from ..state import AgentState
from ..text_utils import content_tokens

_NO_EVIDENCE = (
    "I could not find supported evidence for that question in the sample corpus. "
    "That may mean the topic is outside the 14 documents included here, rather "
    "than that no guidance exists.\n\n" + DISCLAIMER
)


def question_coverage(claim_text: str, question: str) -> float:
    q = set(content_tokens(question))
    if not q:
        return 0.0
    return len(q & set(content_tokens(claim_text))) / len(q)


def compose_answer(state: AgentState, max_claims: int = 6) -> str:
    supported = [v for v in state.verified_claims if v.supported]
    if not supported or not state.chunks:
        return _NO_EVIDENCE

    top_score = max(c.score for c in state.chunks) or 1.0
    chunk_weight = {i + 1: c.score / top_score for i, c in enumerate(state.chunks)}

    def relevance(item) -> float:
        return question_coverage(item.claim.text, state.question) * (
            0.5 + chunk_weight.get(item.claim.citation_index, 0)
        )

    supported = [v for v in supported if question_coverage(v.claim.text, state.question) >= 0.18]
    if not supported:
        return _NO_EVIDENCE
    supported.sort(key=relevance, reverse=True)

    seen: set[str] = set()
    selected = []
    for item in supported:
        key = item.claim.text.lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        selected.append(item)
        if len(selected) >= max_claims:
            break

    lines = [f"Question: {state.question}", "", "What the included sources say:"]
    for item in selected:
        lines.append(f"- {item.claim.text} [{item.claim.citation_index}]")
    lines += ["", "Sources:"]
    for idx, chunk in enumerate(state.chunks, start=1):
        if any(s.claim.citation_index == idx for s in selected):
            lines.append(f"[{idx}] {chunk.title} — {chunk.source}, {chunk.year} ({chunk.doc_id})")
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
