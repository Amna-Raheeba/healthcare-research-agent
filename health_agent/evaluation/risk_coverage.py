"""Risk-coverage evaluation of selective answering.

The bundled eval set (``EVAL_SET``) contains only questions the corpus
*can* answer, so it cannot measure the failure mode abstention exists
for. This module adds ``OUT_OF_CORPUS_SET``: questions about specific
drug dosages, paediatric dosing, and conditions the 14-document sample
corpus does not cover. For those, any composed answer is by construction
unsupported — the corpus contains nothing that could support it.

Definitions, used consistently in the CSV and the notebooks:

- A case counts as **answered** at threshold T if the pipeline, run with
  abstention threshold T, is not blocked, does not abstain, and composes
  an answer containing at least one claim line. (The no-evidence
  fallback therefore counts as not answered, like an abstention.)
- An answered in-corpus case is **correct** if the answer cites its
  expected document; an answered out-of-corpus case is always **wrong**.
- **coverage** = answered / all cases. **risk** = wrong / answered
  (0 when nothing is answered).

The expected shape: as T rises, coverage falls and risk falls with it,
reaching risk 0 while some in-corpus questions are still answered.

Run:  python -m health_agent.evaluation.risk_coverage
Writes results/risk_coverage.csv and prints the table.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from health_agent.config import Config  # noqa: E402
from health_agent.evaluation.evaluate import EVAL_SET  # noqa: E402
from health_agent.graph import run  # noqa: E402

OUT_OF_CORPUS_SET = [
    # Specific drug dosage — the corpus mentions hypothyroidism only in
    # passing (as a condition to exclude when screening for depression).
    {"question": "What is the recommended starting dose of levothyroxine for treating hypothyroidism in adults?", "expected_docs": []},
    # Paediatric dosing — corpus covers adult type 2 diabetes screening,
    # nothing on insulin dosing or children.
    {"question": "How much insulin glargine should a child with type 1 diabetes take at bedtime?", "expected_docs": []},
    # Rare diseases with no document in the corpus.
    {"question": "How is Wilson disease diagnosed and what chelation therapy is used to treat it?", "expected_docs": []},
    {"question": "What are the diagnostic criteria and treatment options for pheochromocytoma?", "expected_docs": []},
    {"question": "What dosage of amoxicillin is prescribed for a toddler with otitis media?", "expected_docs": []},
    {"question": "How is narcolepsy type 1 diagnosed and which wakefulness drugs are first line?", "expected_docs": []},
]

ALL_CASES = [
    {**case, "answerable": True} for case in EVAL_SET
] + [
    {**case, "answerable": False} for case in OUT_OF_CORPUS_SET
]

THRESHOLDS = [0.0, 0.40, 0.50, 0.55, 0.60, 0.62, 0.65, 0.70, 0.80]

_CLAIM_LINE_RE = re.compile(r"^- .+ \[\d+\]\s*$", re.MULTILINE)
_CITATION_RE = re.compile(r"\[(\d+)\]")


def _is_answered(state) -> bool:
    return (
        not state.blocked
        and not state.abstained
        and bool(_CLAIM_LINE_RE.search(state.answer))
    )


def _is_correct(state, case) -> bool:
    cited = {int(n) for n in _CITATION_RE.findall(state.answer.split("Sources:")[0])}
    cited_docs = {
        state.chunks[n - 1].doc_id for n in cited if 1 <= n <= len(state.chunks)
    }
    return any(d in cited_docs for d in case["expected_docs"])


def risk_coverage(cases=ALL_CASES, thresholds=THRESHOLDS, config: Config | None = None) -> list[dict]:
    config = config or Config.from_env()
    rows = []
    for threshold in thresholds:
        cfg = replace(config, abstention_threshold=threshold)
        answered = wrong = 0
        for case in cases:
            state = run(case["question"], cfg)
            if not _is_answered(state):
                continue
            answered += 1
            if not case["answerable"] or not _is_correct(state, case):
                wrong += 1
        rows.append(
            {
                "threshold": threshold,
                "cases": len(cases),
                "answered": answered,
                "coverage": round(answered / len(cases), 3) if cases else 0.0,
                "wrong": wrong,
                "risk": round(wrong / answered, 3) if answered else 0.0,
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["threshold", "cases", "answered", "coverage", "wrong", "risk"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> int:
    rows = risk_coverage()
    out = write_csv(rows, Path(__file__).resolve().parents[2] / "results" / "risk_coverage.csv")
    print(json.dumps(rows, indent=2))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
