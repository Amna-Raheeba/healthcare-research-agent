"""Selective answering: the agent must abstain when evidence is weak.

The out-of-corpus questions here are ones the 14-document sample corpus
cannot answer (a rare disease, a specific drug dose). The in-corpus
question is the best-covered topic in the bundled eval set.
"""
from dataclasses import replace

from health_agent.abstention import assess, evidence_strength
from health_agent.config import Config
from health_agent.graph import run

OUT_OF_CORPUS = "How is Wilson disease diagnosed and what chelation therapy is used to treat it?"
BORDERLINE = "How much insulin glargine should a child with type 1 diabetes take at bedtime?"
IN_CORPUS = "When should adults be screened for type 2 diabetes and which tests are used?"


def test_out_of_corpus_question_abstains():
    state = run(OUT_OF_CORPUS)  # default threshold
    assert not state.blocked  # abstention is not a guardrail block
    assert state.abstained
    assert "doesn't contain enough verified evidence" in state.answer
    assert "Sources:" not in state.answer


def test_well_covered_question_is_not_abstained():
    state = run(IN_CORPUS)
    assert not state.abstained
    assert state.evidence_strength >= Config.from_env().abstention_threshold
    assert "Sources:" in state.answer


def test_threshold_is_respected():
    # The borderline question scores ~0.60: answered under a lenient
    # threshold, abstained under the default one.
    config = Config.from_env()
    lenient = run(BORDERLINE, replace(config, abstention_threshold=0.50))
    assert not lenient.abstained
    strict = run(BORDERLINE, replace(config, abstention_threshold=0.62))
    assert strict.abstained
    assert strict.evidence_strength == lenient.evidence_strength


def test_strength_orders_in_above_out():
    config = Config.from_env()
    in_state = run(IN_CORPUS, replace(config, abstention_threshold=0.0))
    out_state = run(OUT_OF_CORPUS, replace(config, abstention_threshold=0.0))
    assert evidence_strength(in_state) > evidence_strength(out_state)
    assert assess(in_state, 0.62).abstain is False
    assert assess(out_state, 0.62).abstain is True
