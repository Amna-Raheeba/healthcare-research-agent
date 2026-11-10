"""Planner: turn one broad question into focused sub-queries.

A single user question like "When should adults be screened for diabetes
and what test is used?" contains two retrieval intents. Searching with
the raw question alone lets frequent words dominate BM25. Splitting —
plus a small, auditable expansion table for common clinical synonyms —
consistently retrieves the screening-criteria chunk *and* the test chunk.

The expansion table is intentionally explicit, not learned: in a medical
system you want to be able to read exactly why a term was added.
"""
from __future__ import annotations

import re

from ..state import Plan, SubQuery
from ..text_utils import content_tokens

_EXPANSIONS: dict[str, list[str]] = {
    "diabetes": ["diabetes screening HbA1c fasting glucose risk factors"],
    "hba1c": ["HbA1c diagnostic threshold diabetes"],
    "hypertension": ["hypertension blood pressure threshold diagnosis guidelines"],
    "blood": ["blood pressure hypertension measurement"],
    "sepsis": ["sepsis early warning score lactate antibiotics"],
    "radiology": ["radiology imaging artificial intelligence diagnostic accuracy"],
    "cancer": ["cancer screening eligibility early detection"],
    "depression": ["depression screening PHQ-9 primary care"],
    "statin": ["statin cardiovascular risk cholesterol prevention"],
    "kidney": ["chronic kidney disease eGFR albuminuria screening"],
    "stroke": ["stroke recognition FAST thrombolysis time window"],
    "asthma": ["asthma spirometry inhaler management"],
}

_COMPARISON_MARKERS = ("versus", " vs ", "compared with", "difference between", "better than")


def plan_question(question: str) -> Plan:
    lowered = question.lower()
    is_comparison = any(m in lowered for m in _COMPARISON_MARKERS)
    requires_recent = any(w in lowered for w in ("guideline", "current", "latest", "recommend"))

    clauses = [c.strip() for c in re.split(r"\band\b|\?|;", question) if len(c.strip()) > 8]
    sub_queries: list[SubQuery] = [SubQuery(text=question, rationale="original question, unmodified")]

    for clause in clauses:
        if clause.lower() not in question.lower()[: len(clause) + 2] and clause not in [
            s.text for s in sub_queries
        ]:
            sub_queries.append(SubQuery(text=clause, rationale="clause split from compound question"))

    tokens = set(content_tokens(question))
    for key, expansions in _EXPANSIONS.items():
        if key in tokens or key in lowered:
            for exp in expansions:
                if exp not in [s.text for s in sub_queries]:
                    sub_queries.append(SubQuery(text=exp, rationale=f"synonym/facet expansion for '{key}'"))

    # Cap the plan: more sub-queries than this mostly re-retrieve the same docs.
    return Plan(
        original_question=question,
        sub_queries=sub_queries[:5],
        is_comparison=is_comparison,
        requires_recent_guidance=requires_recent,
    )
