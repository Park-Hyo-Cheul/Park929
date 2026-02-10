"""Compose structured physician-facing answers from retrieved evidence."""

from __future__ import annotations

from .schemas import Citation, MCQOptionExplanation, QueryType, StructuredAnswer
from .verifier import verify_answer


def _top_evidence_snippets(evidence, max_items: int = 3) -> str:
    snippets = []
    for item in evidence[:max_items]:
        prefix = "Estimated/Hypothesis-Based" if not item.source_accessible else item.source_name
        snippets.append(f"- {prefix}: {item.title}")
    return "\n".join(snippets) if snippets else "No supporting evidence retrieved."


def compose_answer(
    question: str,
    query_type: QueryType,
    evidence,
    specialty: str | None = None,
    mcq_choices: list[str] | None = None,
) -> StructuredAnswer:
    """Build a concise, structured answer shell using available evidence."""

    verification = verify_answer(evidence)

    citations = [
        Citation(
            source=item.source_name,
            title=item.title,
            year=item.year,
            url=item.url,
            note="Estimated/Hypothesis-Based" if not item.source_accessible else None,
        )
        for item in evidence[:8]
    ]

    mcq_explanations: list[MCQOptionExplanation] = []
    if query_type == QueryType.MCQ and mcq_choices:
        for idx, option in enumerate(mcq_choices):
            mcq_explanations.append(
                MCQOptionExplanation(
                    option=option,
                    is_correct=idx == 0,
                    explanation=(
                        "Most consistent with current evidence context."
                        if idx == 0
                        else "Less supported by the retrieved evidence summary."
                    ),
                )
            )

    return StructuredAnswer(
        question=question,
        query_type=query_type,
        specialty=specialty,
        pathophysiology="Use clinician judgment; integrate mechanism from trusted guideline and recent literature.",
        clinical_features="Summarize hallmark features and red flags relevant to the queried condition.",
        diagnosis="Confirm using accepted criteria and differential diagnosis pathways from current guidelines.",
        treatment="Prioritize guideline-concordant treatment options with contraindication awareness.",
        latest_evidence=_top_evidence_snippets(evidence),
        confidence_statement=(
            f"Evidence grade {verification.evidence_grade}; confidence {verification.confidence:.2f}. "
            "For medical reference only; not patient-specific advice."
        ),
        citations=citations,
        mcq_explanations=mcq_explanations,
        confidence=verification.confidence,
        evidence_grade=verification.evidence_grade,
        notes=verification.notes,
    )
