from datetime import datetime

from cdss.medqna.schemas import EvidenceSource
from cdss.medqna.verifier import verify_answer


def test_verifier_recent_year_bias():
    year = datetime.utcnow().year
    evidence = [
        EvidenceSource(
            source_type="pubmed",
            source_name="PubMed",
            title="Recent",
            summary="",
            year=year,
            source_accessible=True,
        ),
        EvidenceSource(
            source_type="pubmed",
            source_name="PubMed",
            title="Old",
            summary="",
            year=year - 7,
            source_accessible=True,
        ),
    ]

    report = verify_answer(evidence)
    assert report.recent_evidence_ratio == 0.5
    assert report.evidence_grade in {"B", "C"}


def test_verifier_inaccessible_sources_lower_confidence():
    evidence = [
        EvidenceSource(
            source_type="pubmed",
            source_name="PubMed",
            title="Unavailable",
            summary="Estimated/Hypothesis-Based",
            source_accessible=False,
        )
    ]
    report = verify_answer(evidence)
    assert report.confidence <= 0.2
    assert any("Estimated/Hypothesis-Based" in note for note in report.notes)
