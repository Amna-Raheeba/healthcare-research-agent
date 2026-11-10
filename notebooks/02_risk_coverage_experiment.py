"""Notebook 02 — Risk-coverage experiment for selective answering (7 Nov 2026)

Question: does the evidence-strength threshold actually buy safety, and
what does it cost? I.e. as the abstention threshold rises, how much
coverage (fraction of questions answered) do we give up, and how much
does risk (fraction of answered questions that are unsupported) fall?

Method: reuse health_agent.evaluation.risk_coverage over the 6 in-corpus
eval questions + 6 out-of-corpus questions the sample corpus cannot
answer. Writes results/risk_coverage.csv and, if matplotlib is
available, results/risk_coverage.png (risk vs coverage). The plot is a
convenience copy — the CSV is the record of the experiment.

Run from the project root:  python notebooks/02_risk_coverage_experiment.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_agent.evaluation.risk_coverage import risk_coverage, write_csv  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def main() -> int:
    rows = risk_coverage()
    csv_path = write_csv(rows, RESULTS_DIR / "risk_coverage.csv")

    print(f"{'threshold':>9} {'coverage':>9} {'risk':>6} {'answered':>9}")
    for r in rows:
        print(f"{r['threshold']:9.2f} {r['coverage']:9.3f} {r['risk']:6.3f} {r['answered']:9d}")
    print(f"\nwrote {csv_path}")

    png_path = RESULTS_DIR / "risk_coverage.png"
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available — skipping plot, CSV is the record.")
        return 0

    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.plot([r["coverage"] for r in rows], [r["risk"] for r in rows], marker="o")
    for r in rows:
        ax.annotate(f"{r['threshold']:.2f}", (r["coverage"], r["risk"]), textcoords="offset points", xytext=(4, 4), fontsize=7)
    ax.set_xlabel("coverage (fraction answered)")
    ax.set_ylabel("risk (fraction of answered that are unsupported)")
    ax.set_title("Risk-coverage: selective answering\n(12 questions, 14-document sample corpus)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    print(f"wrote {png_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
