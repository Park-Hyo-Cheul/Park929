"""Verification and confidence scoring for medical Q&A outputs."""

from __future__ import annotations

from datetime import datetime

from .schemas import EvidenceSource, VerificationReport

_AUTHORITIES = {"WHO", "AHA/ACC", "ADA", "KDIGO", "NCCN", "EULAR", "PubMed"}


def verify_answer(
    evidence: list[EvidenceSource],
    anatomy_physiology_consistent: bool = True,
) -> VerificationReport:
    """Check recency, authority, and consistency and generate confidence."""

    current_year = datetime.utcnow().year
    recent_cutoff = current_year - 3
    accessible = [item for item in evidence if item.source_accessible]

    recent_count = sum(1 for item in accessible if item.year is not None and item.year >= recent_cutoff)
    recent_ratio = recent_count / len(accessible) if accessible else 0.0

    authority_count = sum(1 for item in accessible if item.source_name in _AUTHORITIES)
    authority_ratio = authority_count / len(accessible) if accessible else 0.0

    consistency_score = 1.0 if anatomy_physiology_consistent else 0.5
    confidence = round(0.5 * recent_ratio + 0.35 * authority_ratio + 0.15 * consistency_score, 2)

    if confidence >= 0.8:
        grade = "A"
    elif confidence >= 0.6:
        grade = "B"
    else:
        grade = "C"

    notes: list[str] = []
    if any(not item.source_accessible for item in evidence):
        notes.append("Some sources were inaccessible; portions are Estimated/Hypothesis-Based.")
    if recent_ratio < 0.5:
        notes.append("Limited evidence from the last 3 years.")
    if not anatomy_physiology_consistent:
        notes.append("Anatomy/physiology consistency checks need manual review.")

    return VerificationReport(
        confidence=confidence,
        evidence_grade=grade,
        recent_evidence_ratio=round(recent_ratio, 2),
        authority_ratio=round(authority_ratio, 2),
        anatomy_physiology_consistent=anatomy_physiology_consistent,
        notes=notes,
    )
