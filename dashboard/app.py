"""Streamlit dashboard for the healthcare research agent.

A thin rendering layer over the real pipeline: every answer shown here
comes from ``health_agent.graph.run`` on the question in the input box
— there are no canned answers. It exists so the pipeline's decisions
(guardrail blocks, abstentions, dropped claims) are visible, not just
the final text; the CLI prints the same run as plain text.

Run it from the project root:

    pip install streamlit
    streamlit run dashboard/app.py

Streamlit is a dashboard-only dependency. The core pipeline
(``health_agent/``) is standard-library only and does not import it.
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

# Streamlit puts this script's folder on sys.path, not the project
# root, so anchor the root (the folder containing health_agent/)
# before importing the pipeline.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

import helpers  # noqa: E402  (dashboard/helpers.py, same folder)
from health_agent.config import Config  # noqa: E402
from health_agent.graph import run  # noqa: E402
from health_agent.guardrails import DISCLAIMER  # noqa: E402

PRESET_QUESTIONS = [
    "When should adults be screened for type 2 diabetes and which tests are used?",
    "How is hypertension diagnosed and what thresholds define it?",
    "How can sepsis be recognised early?",
]

RESULTS_DIR = PROJECT_ROOT / "results"

st.set_page_config(page_title="Healthcare Research Agent", layout="wide")
st.title("Healthcare Research Agent — Verified RAG")
st.warning(DISCLAIMER)
st.caption(
    "Answers are composed only from claims the verifier checked against "
    "the 14-document sample corpus. This is an engineering demonstration, "
    "not a clinical tool."
)

# --- Sidebar: presets + the one knob worth showing -------------------
with st.sidebar:
    st.header("Example questions")
    for preset in PRESET_QUESTIONS:
        if st.button(preset, use_container_width=True):
            st.session_state["question"] = preset
    st.caption(
        "To see the safety states, try a personal-diagnosis request "
        "(\"Do I have diabetes? Diagnose me\") or an out-of-corpus "
        "question (e.g. about Wilson disease) for the abstention state."
    )
    st.divider()
    threshold = st.slider(
        "Abstention threshold (evidence strength)",
        min_value=0.0,
        max_value=1.0,
        value=Config.from_env().abstention_threshold,
        step=0.01,
        help="Below this evidence-strength score the agent abstains "
        "instead of composing an answer. Default 0.62.",
    )

question = st.text_input(
    "General healthcare research question",
    key="question",
    placeholder="Ask a general question the sample corpus might cover…",
)

if question:
    config = replace(Config.from_env(), abstention_threshold=threshold)
    state = run(question, config)
    status = helpers.run_status(state)

    st.divider()
    if status == "blocked":
        label = {
            "emergency": "Guardrail: emergency",
            "personal_diagnosis": "Guardrail: personal diagnosis",
        }.get(state.block_reason, "Guardrail")
        st.error(f"**{label}** — the question was stopped before retrieval.")
        st.write(state.answer)
    elif status == "abstained":
        st.warning("**ABSTAINED** — the evidence was too weak to answer reliably.")
        col1, col2 = st.columns(2)
        col1.metric("Evidence strength", f"{state.evidence_strength:.2f}")
        col2.metric("Abstention threshold", f"{threshold:.2f}")
        st.write(f"Reason: {state.abstention_reason}")
        st.write(state.answer)
    else:
        st.success("Answered from verified claims only.")
        st.metric("Evidence strength", f"{state.evidence_strength:.2f}")
        claims = helpers.parse_answer_claims(state.answer)
        if claims:
            st.subheader("Answer — verified claims")
            for claim in claims:
                st.markdown(
                    f"- {helpers.format_claim(claim['text'], claim['citation_index'])}"
                )
            sources = helpers.format_sources(state)
            if sources:
                st.subheader("Sources")
                for line in sources:
                    st.markdown(f"- {line}")
        else:
            # Answered state but the composer found no usable evidence.
            st.write(state.answer)

    # --- Pipeline trace ---------------------------------------------
    with st.expander("Pipeline trace — planner, retrieval, verifier"):
        st.markdown("**Trace steps**")
        st.dataframe(helpers.trace_rows(state), use_container_width=True)

        st.markdown("**Planner sub-queries**")
        queries = helpers.sub_queries(state)
        if queries:
            st.dataframe(queries, use_container_width=True)
        else:
            st.caption("No plan — the run stopped at the guardrails.")

        st.markdown("**Retrieved chunks (BM25)**")
        chunks = helpers.retrieved_chunks(state)
        if chunks:
            st.dataframe(chunks, use_container_width=True)
        else:
            st.caption("No chunks retrieved.")

        st.markdown("**Verifier decisions (per claim)**")
        decisions = helpers.verifier_decisions(state)
        if decisions:
            st.dataframe(decisions, use_container_width=True)
        else:
            st.caption("No claims were extracted.")

# --- Results panel: selective answering -------------------------------
st.divider()
st.header("Selective answering — risk–coverage results")
st.caption(
    "From notebooks/02_risk_coverage_experiment.py: 6 in-corpus + 6 "
    "out-of-corpus questions, swept over the abstention threshold. "
    "Risk = fraction of answered questions whose answers were "
    "unsupported; coverage = fraction answered at all."
)
rows = helpers.load_risk_coverage(RESULTS_DIR / "risk_coverage.csv")
if rows:
    st.dataframe(rows, use_container_width=True)
else:
    st.info(
        "results/risk_coverage.csv not found — run "
        "`python -m health_agent.evaluation.risk_coverage` to generate it."
    )
plot_path = RESULTS_DIR / "risk_coverage.png"
if plot_path.exists():
    st.image(str(plot_path), caption="Risk vs coverage as the abstention threshold rises")

st.divider()
st.caption(DISCLAIMER)
