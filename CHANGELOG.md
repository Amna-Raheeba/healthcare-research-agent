# Changelog

## v0.3.0 — 2026-11-10 — Streamlit dashboard

- Added `dashboard/`: a Streamlit front-end that runs the real
  pipeline (`health_agent.graph.run`) — question input with preset
  questions, verified claims with citations and sources, visibly
  distinct guardrail and ABSTAINED states (with evidence strength and
  reason), a live abstention-threshold slider, a pipeline-trace view
  (planner sub-queries, BM25 chunks, per-claim verifier decisions),
  and the risk–coverage results panel.
- `dashboard/helpers.py` keeps the formatting and CSV-loading logic
  Streamlit-free and unit-tested (`tests/test_dashboard_helpers.py`).
- Streamlit is a dashboard-only dependency: it is not in the core
  `requirements.txt` and nothing in `health_agent/` imports it.

## v0.2.0 — 10 Nov 2026

**Selective answering + risk–coverage evaluation.**

- Added `health_agent/abstention.py`: after verification, an
  evidence-strength score (verifier support of usable claims, question
  coverage, retrieval saturation) is compared against a configurable
  threshold (`HEALTH_AGENT_ABSTAIN_THRESHOLD`, default 0.62). Below it,
  the agent abstains with an explicit message instead of composing an
  answer from weakly related chunks. Guardrails still run first and are
  unchanged — a blocked question is blocked, never merely abstained.
- CLI and JSON output now report `abstained`, `evidence_strength`, and
  `abstention_reason`; `AgentState` carries the same fields.
- Added risk–coverage evaluation (`health_agent/evaluation/risk_coverage.py`):
  the 6 in-corpus eval questions plus 6 out-of-corpus questions (drug
  dosages, paediatric dosing, rare diseases) swept over 9 thresholds.
  Results in `results/risk_coverage.csv`: risk falls from 0.455 at
  coverage 0.917 to 0.0 at coverage 0.5. The default threshold sits in
  that zero-risk region.
- Added researcher notebooks (`notebooks/01_*` retrieval failure
  analysis, `notebooks/02_*` risk–coverage experiment with plot).
- CI hardening: `pythonpath` in the pytest config plus a root
  `conftest.py`, so the suite passes under the bare `pytest` binary
  that GitHub Actions runs, not only under `python -m pytest`.

## v0.1.0 — 30 Oct 2026

**Initial verified RAG.**

- Pipeline: guardrails → planner → BM25 retriever → claim verifier →
  answer composer, pure Python, no API key required.
- Verifier checks every claim against its cited chunk, with numbers
  checked separately so invented statistics and thresholds are rejected.
- Medical guardrails before retrieval: emergency safe completion,
  personal-diagnosis refusal, disclaimer on every answer.
- 14-document hand-written sample corpus, 6-question eval set
  (retrieval recall, citation precision, faithfulness), 15 tests.
