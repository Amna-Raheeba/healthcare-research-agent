# Dashboard

A Streamlit front-end for the healthcare research agent, in the same
spirit as the results dashboard in my FYP repo: a way to *watch the
pipeline decide*, not just read its final answer.

## What it shows

- **Ask a question** (or pick one of three preset questions drawn from
  the corpus topics) and run the real pipeline — every answer comes
  from `health_agent.graph.run`, nothing is canned.
- **Verified claims with citations** — the answer area lists only the
  claims the verifier supported, each with its `[n]` citation, plus
  the matching source list.
- **The three safety states, visibly distinct:**
  - a red **guardrail** panel for personal-diagnosis and emergency
    inputs (stopped before retrieval);
  - an **ABSTAINED** panel with the evidence-strength score and the
    reason, when selective answering refuses a weakly supported
    question;
  - the abstention threshold is a sidebar slider, so the trade-off can
    be explored live.
- **Pipeline trace** (expander): per-stage timing, the planner's
  sub-queries and why each was created, the retrieved chunks with
  their BM25 scores, and the verifier's per-claim decision
  (supported / dropped, with support ratio and reason).
- **Results panel**: the risk–coverage table from
  `results/risk_coverage.csv` and its plot — risk falling to 0.0 as
  the threshold rises and coverage falls (see the main README's
  Evaluation section for the honest framing of those numbers).
- The medical disclaimer is shown at the top and bottom of the page.

## Run it

From the project root:

```bash
pip install streamlit
streamlit run dashboard/app.py
```

## Notes

- Streamlit is a **dashboard-only** dependency. The core pipeline is
  standard-library only; nothing in `health_agent/` imports it, and it
  is deliberately not in the core `requirements.txt`.
- `helpers.py` holds the formatting/loading logic with no Streamlit
  import, so it is covered by the normal test suite
  (`tests/test_dashboard_helpers.py`).
- If `results/risk_coverage.csv` is missing (a fresh clone where the
  evaluation has not been run), the results panel says so and points
  at the command that generates it instead of failing.
