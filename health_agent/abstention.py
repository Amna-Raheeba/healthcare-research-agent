"""Selective answering: abstain when the evidence is too weak.

Verification answers a per-claim question — *is this sentence supported by
its citation?* It does not answer the prior question: *was there enough
relevant evidence in the corpus to answer at all?* A question about a
topic the corpus barely touches can still retrieve a few chunks, and the
sentences in those chunks verify trivially against themselves, so the
old pipeline would compose a confident-looking answer from
near-irrelevant material.

This module scores the *strength* of the evidence behind a would-be
answer, after verification and before composition:

    strength = 0.35 * mean verifier support of the claims the composer
                      would actually use (supported claims that cover the
                      question)
             + 0.30 * best question coverage among those claims
             + 0.20 * mean question coverage among those claims
             + 0.15 * retrieval saturation, top_score / (top_score + 4),
                      which maps the unbounded BM25 score onto [0, 1)

If no claim survives the composer's relevance filter, strength is 0.
Below ``Config.abstention_threshold`` the agent abstains with an explicit
message instead of composing. This is the selective-prediction /
risk-coverage trade-off from the selective classification literature
applied to RAG: coverage falls, risk on the answered questions falls
with it. The sweep in ``health_agent.evaluation.risk_coverage`` measures
exactly that on the bundled cases.

Guardrails are unaffected: they run before retrieval, so an emergency or
a personal-diagnosis request is still blocked, never merely abstained.
"""
from __future__ import annotations

from dataclasses import dataclass

from .agents.answer import question_coverage
from .guardrails import DISCLAIMER
from .state import AgentState

# Same relevance floor the answer composer applies: a claim that covers
# less of the question than this would not be used in the answer anyway.
_MIN_COVERAGE = 0.18

ABSTAIN_MESSAGE = (
    "I'm going to abstain on this one: the sample corpus doesn't contain "
    "enough verified evidence to answer this reliably. The retrieved "
    "material is only weakly related to the question, so composing an "
    "answer from it would risk stating things the sources do not actually "
    "support. A broader corpus — or a clinician, if this is about a "
    "specific person's care — is the right source here."
)


@dataclass
class AbstentionDecision:
    abstain: bool
    strength: float
    reason: str


def relevant_supported(state: AgentState):
    """Supported claims that pass the composer's question-coverage floor."""
    return [
        v
        for v in state.verified_claims
        if v.supported and question_coverage(v.claim.text, state.question) >= _MIN_COVERAGE
    ]


def evidence_strength(state: AgentState) -> float:
    """Evidence-strength score in [0, 1] for the answer ``state`` would give."""
    if not state.chunks:
        return 0.0
    usable = relevant_supported(state)
    if not usable:
        return 0.0
    mean_support = sum(v.support_ratio for v in usable) / len(usable)
    coverages = [question_coverage(v.claim.text, state.question) for v in usable]
    top_score = max(c.score for c in state.chunks)
    retrieval_saturation = top_score / (top_score + 4.0) if top_score > 0 else 0.0
    strength = (
        0.35 * mean_support
        + 0.30 * max(coverages)
        + 0.20 * (sum(coverages) / len(coverages))
        + 0.15 * retrieval_saturation
    )
    return round(min(max(strength, 0.0), 1.0), 4)


def assess(state: AgentState, threshold: float) -> AbstentionDecision:
    """Decide whether ``state`` has enough evidence to answer at ``threshold``."""
    strength = evidence_strength(state)
    if strength < threshold:
        if not state.chunks:
            reason = "no chunks retrieved"
        elif not relevant_supported(state):
            reason = "no supported claim covers the question"
        else:
            reason = "retrieved evidence is only weakly related to the question"
        return AbstentionDecision(
            abstain=True,
            strength=strength,
            reason=f"evidence strength {strength:.2f} below threshold {threshold:.2f} ({reason})",
        )
    return AbstentionDecision(
        abstain=False,
        strength=strength,
        reason=f"evidence strength {strength:.2f} at or above threshold {threshold:.2f}",
    )


def abstain_answer(decision: AbstentionDecision) -> str:
    return ABSTAIN_MESSAGE + "\n\n" + DISCLAIMER
