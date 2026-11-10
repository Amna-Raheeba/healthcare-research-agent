from health_agent.agents.verifier import verify_claim
from health_agent.state import Claim, RetrievedChunk


def _chunk():
    return RetrievedChunk(
        doc_id="doc-001", title="Diabetes screening", source="Sample", year=2024,
        text="An HbA1c of 6.5% or higher supports a diagnosis of diabetes when confirmed on repeat testing.",
        score=5.0, matched_query="diabetes",
    )


def test_claim_copied_from_source_is_supported():
    chunk = _chunk()
    claim = Claim(text="An HbA1c of 6.5% or higher supports a diagnosis of diabetes when confirmed on repeat testing.", citation_index=1)
    result = verify_claim(claim, [chunk])
    assert result.supported


def test_fabricated_claim_is_flagged_unsupported():
    chunk = _chunk()
    claim = Claim(text="Patients should inject 40 units of insulin every morning regardless of glucose readings.", citation_index=1)
    result = verify_claim(claim, [chunk])
    assert not result.supported


def test_invented_number_is_flagged():
    chunk = _chunk()
    claim = Claim(text="An HbA1c of 9.9% or higher supports a diagnosis of diabetes when confirmed on repeat testing.", citation_index=1)
    result = verify_claim(claim, [chunk])
    assert not result.supported
    assert "number" in result.reason
