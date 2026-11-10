import re

from health_agent.graph import run


def test_answer_contains_citations_and_sources():
    state = run("When should adults be screened for type 2 diabetes and which tests are used?")
    assert not state.blocked
    assert re.search(r"\[\d+\]", state.answer)
    assert "Sources:" in state.answer
    assert "doc-001" in state.answer


def test_answer_only_uses_verified_claims():
    state = run("How is hypertension diagnosed and what thresholds define it?")
    supported_texts = {v.claim.text for v in state.verified_claims if v.supported}
    for line in state.answer.splitlines():
        if line.startswith("- "):
            claim_text = re.sub(r"\s*\[\d+\]\s*$", "", line[2:])
            assert claim_text in supported_texts


def test_trace_records_pipeline_order():
    state = run("How can sepsis be recognised early?")
    agents = [t.agent for t in state.trace]
    assert agents == ["guardrails", "planner", "retriever", "verifier", "answer"]


def test_out_of_corpus_question_admits_limits():
    state = run("What is the capital of France and when was it founded?")
    # Either no supported evidence, or an answer that still carries the disclaimer.
    assert "Disclaimer" in state.answer
