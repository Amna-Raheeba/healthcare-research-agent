"""Pure-Python helpers for the Streamlit dashboard.

Everything in this module works on plain data — the pipeline's
``AgentState``, answer text, and the risk–coverage CSV — with no
Streamlit import, so the formatting and loading logic can be
unit-tested without a browser or a server (see
``tests/test_dashboard_helpers.py``). ``dashboard/app.py`` is a thin
rendering layer over these functions.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

# Answer bullets are composed by health_agent/agents/answer.py as
# "- <claim text> [<citation index>]".
_CLAIM_LINE = re.compile(r"^- (?P<text>.+?) \[(?P<index>\d+)\]\s*$")

# Columns of results/risk_coverage.csv, written by
# health_agent/evaluation/risk_coverage.py.
_INT_COLUMNS = {"cases", "answered", "wrong"}
_FLOAT_COLUMNS = {"threshold", "coverage", "risk"}


def run_status(state) -> str:
    """One-word status for a finished run: blocked | abstained | answered."""
    if state.blocked:
        return "blocked"
    if state.abstained:
        return "abstained"
    return "answered"


def parse_answer_claims(answer: str) -> list[dict]:
    """Extract the cited claim bullets from a composed answer.

    Returns ``[{"text": ..., "citation_index": ...}, ...]`` in answer
    order. The abstention message, the guardrail messages, and the
    no-evidence answer contain no such bullets, so they return ``[]`` —
    which is exactly how the dashboard knows there is nothing to list.
    """
    claims = []
    for line in answer.splitlines():
        match = _CLAIM_LINE.match(line.strip())
        if match:
            claims.append(
                {
                    "text": match.group("text"),
                    "citation_index": int(match.group("index")),
                }
            )
    return claims


def format_claim(text: str, citation_index: int | None) -> str:
    """Render one claim the way the CLI answer does: text plus [n]."""
    if citation_index is None:
        return text
    return f"{text} [{citation_index}]"


def format_sources(state) -> list[str]:
    """Source lines for the chunks cited by the answer's claims.

    Mirrors the "Sources:" section format of the text answer:
    ``[n] Title — Source, Year (doc-id)``, restricted to the citation
    indices that actually appear in the answer, in index order.
    """
    cited = {c["citation_index"] for c in parse_answer_claims(state.answer)}
    citation_map = state.citation_map()
    lines = []
    for index in sorted(cited):
        chunk = citation_map.get(index)
        if chunk is not None:
            lines.append(
                f"[{index}] {chunk.title} — {chunk.source}, {chunk.year} ({chunk.doc_id})"
            )
    return lines


def verifier_decisions(state) -> list[dict]:
    """Per-claim verifier outcome, for the pipeline-trace view."""
    return [
        {
            "claim": v.claim.text,
            "citation_index": v.claim.citation_index,
            "status": "supported" if v.supported else "dropped",
            "support_ratio": round(v.support_ratio, 3),
            "supporting_doc_id": v.supporting_doc_id or "",
            "reason": v.reason,
        }
        for v in state.verified_claims
    ]


def retrieved_chunks(state) -> list[dict]:
    """Retrieved chunks with their BM25 scores, in citation order."""
    return [
        {
            "index": i + 1,
            "doc_id": chunk.doc_id,
            "title": chunk.title,
            "score": round(chunk.score, 3),
            "matched_query": chunk.matched_query,
        }
        for i, chunk in enumerate(state.chunks)
    ]


def sub_queries(state) -> list[dict]:
    """Planner output: each sub-query and why the planner created it."""
    if state.plan is None:
        return []
    return [
        {"sub_query": sq.text, "rationale": sq.rationale}
        for sq in state.plan.sub_queries
    ]


def trace_rows(state) -> list[dict]:
    """Pipeline trace steps as plain dicts (agent, action, ms)."""
    return [
        {
            "agent": step.agent,
            "action": step.action,
            "detail": step.detail,
            "duration_ms": round(step.duration_ms, 2),
        }
        for step in state.trace
    ]


def load_risk_coverage(path: str | Path) -> list[dict]:
    """Load results/risk_coverage.csv as typed rows.

    Returns ``[]`` when the file does not exist (the dashboard renders
    an explanatory note instead of failing on a fresh clone where the
    evaluation has not been run yet). Numeric columns are converted:
    counts to ``int``, rates and thresholds to ``float``.
    """
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = {}
            for key, value in raw.items():
                if key in _INT_COLUMNS:
                    row[key] = int(value)
                elif key in _FLOAT_COLUMNS:
                    row[key] = float(value)
                else:
                    row[key] = value
            rows.append(row)
    return rows
