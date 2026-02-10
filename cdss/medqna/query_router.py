"""Simple query routing for medical Q&A requests."""

from __future__ import annotations

import re

from .schemas import QueryType


_DRUG_COMPARE_PATTERNS = (
    r"\b(vs|versus|compare|comparison|better than|difference between)\b",
)


def route_query(question: str, mcq_mode: bool = False, choices: list[str] | None = None) -> QueryType:
    """Route query to general, MCQ, or drug-comparison workflows."""

    text = question.strip().lower()
    normalized_choices = [c for c in (choices or []) if c.strip()]

    if mcq_mode or normalized_choices or re.search(r"\b(a\)|b\)|c\)|d\))", text):
        return QueryType.MCQ

    if any(re.search(pattern, text) for pattern in _DRUG_COMPARE_PATTERNS) and (
        "drug" in text or "dose" in text or "statin" in text or "insulin" in text
    ):
        return QueryType.DRUG_COMPARISON

    return QueryType.GENERAL
