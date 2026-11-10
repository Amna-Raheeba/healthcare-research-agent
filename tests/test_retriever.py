from health_agent.agents.retriever import BM25Index
from health_agent.config import Config
from health_agent.tools.corpus import load_corpus


def _index():
    return BM25Index(load_corpus(Config.from_env().corpus_path))


def test_diabetes_query_retrieves_diabetes_doc_first():
    results = _index().search("diabetes screening HbA1c fasting glucose", top_k=3)
    assert results
    assert results[0][0].doc_id == "doc-001"


def test_sepsis_query_retrieves_sepsis_doc():
    results = _index().search("sepsis early recognition lactate antibiotics first hour", top_k=3)
    assert "doc-005" in [d.doc_id for d, _ in results]


def test_irrelevant_query_scores_low_or_empty():
    results = _index().search("quantum entanglement photon teleportation", top_k=3)
    # BM25 may return weak matches on shared stopword-like tokens, but the
    # top score for an off-topic query must be far below an on-topic one.
    on_topic = _index().search("diabetes screening HbA1c", top_k=1)[0][1]
    if results:
        assert results[0][1] < on_topic
