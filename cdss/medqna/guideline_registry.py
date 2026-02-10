"""Curated guideline registry for medical Q&A."""

from __future__ import annotations

from dataclasses import dataclass

import requests

from .schemas import EvidenceSource


@dataclass(frozen=True)
class GuidelineSource:
    authority: str
    title: str
    url: str
    specialty: str


CURATED_GUIDELINES: tuple[GuidelineSource, ...] = (
    GuidelineSource("WHO", "WHO Guidelines", "https://www.who.int/publications/guidelines", "general"),
    GuidelineSource("AHA/ACC", "AHA/ACC Guidelines", "https://www.ahajournals.org/guidelines", "cardiology"),
    GuidelineSource("ADA", "ADA Standards of Care", "https://diabetesjournals.org/care/issue", "endocrinology"),
    GuidelineSource("KDIGO", "KDIGO Guidelines", "https://kdigo.org/guidelines/", "nephrology"),
    GuidelineSource("NCCN", "NCCN Guidelines", "https://www.nccn.org/guidelines", "oncology"),
    GuidelineSource("EULAR", "EULAR Recommendations", "https://www.eular.org/recommendations", "rheumatology"),
)


def get_guidelines(specialty: str | None = None, user_links: list[str] | None = None) -> list[EvidenceSource]:
    specialty = (specialty or "general").lower()
    evidence: list[EvidenceSource] = []

    for g in CURATED_GUIDELINES:
        if g.specialty == "general" or specialty == "all" or specialty == g.specialty:
            evidence.append(
                EvidenceSource(
                    source_type="guideline",
                    source_name=g.authority,
                    title=g.title,
                    summary=f"Official guideline source for {g.specialty}.",
                    url=g.url,
                    source_accessible=True,
                )
            )

    for link in user_links or []:
        evidence.append(
            EvidenceSource(
                source_type="guideline",
                source_name="User-provided",
                title="User-provided guideline",
                summary="User provided external guideline link.",
                url=link,
                source_accessible=True,
            )
        )

    return evidence


def try_fetch_guideline(url: str, timeout: int = 10) -> str | None:
    """Optionally fetch a guideline page for basic availability checks."""

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except Exception:
        return None

    return response.text[:1000]
