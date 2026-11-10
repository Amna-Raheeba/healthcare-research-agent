"""Graph runner: guardrails -> planner -> retriever -> verifier -> answer.

Written as a plain function pipeline rather than a LangGraph graph so it
runs anywhere Python runs, with no API key. The node boundaries mirror
exactly the graph you would declare in LangGraph (each step takes and
returns ``AgentState``), which makes a later port mechanical.
"""
from __future__ import annotations

from .agents.answer import compose_answer
from .agents.planner import plan_question
from .agents.retriever import BM25Index, retrieve
from .agents.verifier import extract_claims, verify_claims
from .config import Config
from .guardrails import DISCLAIMER, check_input
from .observability import traced
from .state import AgentState
from .tools.corpus import load_corpus


def run(question: str, config: Config | None = None) -> AgentState:
    config = config or Config.from_env()
    state = AgentState(question=question)

    with traced(state, "guardrails", "check_input", question[:60]):
        verdict = check_input(question)
    if not verdict.allowed:
        state.blocked = True
        state.block_reason = verdict.category
        state.answer = verdict.message + "\n\n" + DISCLAIMER
        return state

    with traced(state, "planner", "plan_question"):
        state.plan = plan_question(question)

    documents = load_corpus(config.corpus_path)
    index = BM25Index(documents)
    with traced(state, "retriever", "bm25_search", f"{len(state.plan.sub_queries)} sub-queries"):
        state.chunks = retrieve(state.plan, index, config.top_k_per_query, config.max_chunks)

    with traced(state, "verifier", "extract_and_verify"):
        state.draft_claims = extract_claims(state.chunks)
        state.verified_claims = verify_claims(state.draft_claims, state.chunks, config.min_support_ratio)

    with traced(state, "answer", "compose_from_verified_only"):
        state.answer = compose_answer(state)
    return state
