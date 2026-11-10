"""Dashboard helpers: formatting and CSV loading, no Streamlit needed.

These import dashboard/helpers.py by path manipulation rather than as
a package — the dashboard folder is a Streamlit script folder, not
part of the health_agent package.
"""
import importlib.util
from pathlib import Path

from health_agent.graph import run

_HELPERS_PATH = Path(__file__).resolve().parent.parent / "dashboard" / "helpers.py"
_spec = importlib.util.spec_from_file_location("dashboard_helpers", _HELPERS_PATH)
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)

_RESULTS_CSV = Path(__file__).resolve().parent.parent / "results" / "risk_coverage.csv"


def test_parse_answer_claims_extracts_cited_bullets():
    state = run("When should adults be screened for type 2 diabetes and which tests are used?")
    claims = helpers.parse_answer_claims(state.answer)
    assert claims, "a composed answer should yield cited claims"
    for claim in claims:
        assert claim["text"]
        assert claim["citation_index"] >= 1
        # Round-trips back to the line format used in the answer.
        assert helpers.format_claim(claim["text"], claim["citation_index"]) in state.answer


def test_format_claim_with_and_without_citation():
    assert helpers.format_claim("Some claim.", 3) == "Some claim. [3]"
    assert helpers.format_claim("Some claim.", None) == "Some claim."


def test_abstained_and_blocked_answers_have_no_claims():
    abstained = run("How is Wilson disease diagnosed and what chelation therapy is used to treat it?")
    assert helpers.run_status(abstained) == "abstained"
    assert helpers.parse_answer_claims(abstained.answer) == []
    assert helpers.format_sources(abstained) == []

    blocked = run("Do I have diabetes? Diagnose me")
    assert helpers.run_status(blocked) == "blocked"
    assert helpers.parse_answer_claims(blocked.answer) == []


def test_sources_match_answer_citations():
    state = run("How can sepsis be recognised early?")
    assert helpers.run_status(state) == "answered"
    cited = {c["citation_index"] for c in helpers.parse_answer_claims(state.answer)}
    sources = helpers.format_sources(state)
    assert sources, "answered run should render its sources"
    for line in sources:
        index = int(line.split("]")[0].lstrip("["))
        assert index in cited
        assert "(" in line and ")" in line  # carries the doc-id


def test_verifier_decisions_cover_every_claim():
    state = run("How is hypertension diagnosed and what thresholds define it?")
    decisions = helpers.verifier_decisions(state)
    assert len(decisions) == len(state.verified_claims)
    assert {d["status"] for d in decisions} <= {"supported", "dropped"}
    chunks = helpers.retrieved_chunks(state)
    assert [c["index"] for c in chunks] == list(range(1, len(state.chunks) + 1))


def test_load_risk_coverage_typed_rows_and_missing_file(tmp_path):
    rows = helpers.load_risk_coverage(_RESULTS_CSV)
    assert rows, "the committed results CSV should load"
    first = rows[0]
    assert isinstance(first["threshold"], float)
    assert isinstance(first["cases"], int)
    assert isinstance(first["risk"], float)
    # The sweep's story: risk at the loosest threshold is the highest.
    assert rows[0]["risk"] >= rows[-1]["risk"]

    assert helpers.load_risk_coverage(tmp_path / "does_not_exist.csv") == []
