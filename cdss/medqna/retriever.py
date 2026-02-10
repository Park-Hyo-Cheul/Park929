"""Evidence retrieval orchestration for medical Q&A."""

from __future__ import annotations

from .guideline_registry import get_guidelines
from .pubmed_client import PubMedClient
from .schemas import EvidenceSource


def retrieve_evidence(
    question: str,
    specialty: str | None = None,
    user_guideline_links: list[str] | None = None,
    pubmed_max_results: int = 5,
) -> list[EvidenceSource]:
    """Merge PubMed and guideline evidence into one context list."""

    evidence: list[EvidenceSource] = []

    client = PubMedClient()
    try:
        evidence.extend(client.retrieve(question, max_results=pubmed_max_results))
    except Exception:
        evidence.append(
            EvidenceSource(
                source_type="pubmed",
                source_name="PubMed",
                title="PubMed retrieval unavailable",
                summary="Estimated/Hypothesis-Based: live PubMed retrieval failed in this run.",
                source_accessible=False,
            )
        )

    evidence.extend(get_guidelines(specialty=specialty, user_links=user_guideline_links))
    return evidence
