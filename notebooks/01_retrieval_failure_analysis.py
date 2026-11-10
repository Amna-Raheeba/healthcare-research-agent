"""Notebook 01 — Where does retrieval fail? (4 Nov 2026)

Question: for which eval questions does BM25 retrieve weakly — the
expected document missing entirely, retrieved with a thin margin over
the runner-up, or dragged down by generic matches? Those are the cases
where a composed answer would rest on shaky evidence, so they are also
the cases selective answering (notebook 02) has to catch.

Method: run every case from the bundled eval set plus the out-of-corpus
set through the real pipeline at threshold 0 (abstention disabled, so
nothing is hidden) and print a per-question diagnostic table, then list
the misses explicitly.

Run from the project root:  python notebooks/01_retrieval_failure_analysis.py
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_agent.config import Config  # noqa: E402
from health_agent.evaluation.evaluate import EVAL_SET  # noqa: E402
from health_agent.evaluation.risk_coverage import OUT_OF_CORPUS_SET  # noqa: E402
from health_agent.graph import run  # noqa: E402

MARGIN_FLOOR = 0.15  # (top - second) / top below this counts as a weak win


def diagnose(question: str, expected_docs: list[str], config: Config) -> dict:
    state = run(question, config)
    scores = [c.score for c in state.chunks]
    top = scores[0] if scores else 0.0
    margin = (top - scores[1]) / top if len(scores) > 1 and top > 0 else 1.0
    retrieved = [c.doc_id for c in state.chunks]
    return {
        "question": question,
        "expected": expected_docs,
        "retrieved": retrieved,
        "hit": any(d in retrieved for d in expected_docs) if expected_docs else None,
        "top_score": round(top, 3),
        "margin": round(margin, 3),
        "strength": state.evidence_strength,
    }


def main() -> int:
    config = replace(Config.from_env(), abstention_threshold=0.0)
    rows = [diagnose(c["question"], c["expected_docs"], config) for c in EVAL_SET]
    rows += [diagnose(c["question"], c["expected_docs"], config) for c in OUT_OF_CORPUS_SET]

    print(f"{'strength':>8} {'margin':>7} {'top':>7}  question")
    for r in rows:
        print(f"{r['strength']:8.3f} {r['margin']:7.3f} {r['top_score']:7.2f}  {r['question'][:76]}")

    print("\n--- misses ---")
    misses = 0
    for r in rows:
        problems = []
        if r["hit"] is False:
            problems.append(f"expected {r['expected']} not retrieved (got {r['retrieved']})")
        if r["expected"] and r["margin"] < MARGIN_FLOOR:
            problems.append(f"thin retrieval margin {r['margin']:.3f}")
        if not r["expected"] and r["strength"] > 0:
            problems.append(
                f"out-of-corpus but retrieved {r['retrieved']} with strength {r['strength']:.3f}"
                " — abstention has to catch this one"
            )
        if not r["retrieved"]:
            problems.append("nothing retrieved at all")
        if problems:
            misses += 1
            print(f"* {r['question'][:76]}")
            for p in problems:
                print(f"    - {p}")
    print(f"\n{misses} of {len(rows)} questions show a retrieval weakness worth noting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
