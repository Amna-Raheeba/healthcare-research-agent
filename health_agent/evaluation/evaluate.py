"""Offline evaluation on the bundled eval set.

Metrics, defined plainly:
- retrieval_recall_at_k: fraction of cases where an expected doc is in the chunks.
- citation_precision: fraction of citations in the final answer that point to a
  chunk whose doc was expected *or* that passed verification for that claim.
- faithfulness: supported claims / total draft claims for the retrieved set.

Run:  python -m health_agent.evaluation.evaluate
These numbers describe this sample corpus and this eval set only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from health_agent.config import Config  # noqa: E402
from health_agent.graph import run  # noqa: E402

EVAL_SET = [
    {"question": "When should adults be screened for type 2 diabetes and which tests are used?", "expected_docs": ["doc-001"]},
    {"question": "How is hypertension diagnosed and what blood pressure thresholds define it?", "expected_docs": ["doc-003"]},
    {"question": "How can sepsis be recognised early and what should happen in the first hour?", "expected_docs": ["doc-005"]},
    {"question": "What are the benefits and limitations of AI in radiology imaging?", "expected_docs": ["doc-007"]},
    {"question": "Who should be screened for colorectal cancer and at what age does screening start?", "expected_docs": ["doc-009"]},
    {"question": "How is depression screened for in primary care?", "expected_docs": ["doc-011"]},
]

_CITATION_RE = re.compile(r"\[(\d+)\]")


def evaluate(cases=EVAL_SET, config: Config | None = None) -> dict:
    config = config or Config.from_env()
    recalls, precisions, faithfulness_scores = [], [], []
    per_case = []
    for case in cases:
        state = run(case["question"], config)
        retrieved_ids = [c.doc_id for c in state.chunks]
        hit = any(d in retrieved_ids for d in case["expected_docs"])
        recalls.append(1.0 if hit else 0.0)

        cited = [int(n) for n in _CITATION_RE.findall(state.answer.split("Sources:")[0])]
        if cited:
            good = 0
            for n in cited:
                if 1 <= n <= len(state.chunks):
                    chunk = state.chunks[n - 1]
                    verified = any(
                        v.supported and v.claim.citation_index == n for v in state.verified_claims
                    )
                    if verified or chunk.doc_id in case["expected_docs"]:
                        good += 1
            precisions.append(good / len(cited))
        total = len(state.verified_claims)
        faithfulness_scores.append(
            (sum(1 for v in state.verified_claims if v.supported) / total) if total else 0.0
        )
        per_case.append({"question": case["question"], "retrieval_hit": hit, "retrieved": retrieved_ids})

    return {
        "cases": len(cases),
        "retrieval_recall_at_k": round(sum(recalls) / len(recalls), 3) if recalls else 0.0,
        "citation_precision": round(sum(precisions) / len(precisions), 3) if precisions else 0.0,
        "faithfulness_supported_ratio": round(sum(faithfulness_scores) / len(faithfulness_scores), 3) if faithfulness_scores else 0.0,
        "per_case": per_case,
        "note": "Measured only on the bundled eval set against the sample corpus.",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
