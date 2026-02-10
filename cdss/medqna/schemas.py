"""Schemas for the medical Q&A layer."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class QueryType(str, Enum):
    GENERAL = "general"
    MCQ = "mcq"
    DRUG_COMPARISON = "drug_comparison"


class Citation(BaseModel):
    source: str
    title: str
    year: int | None = None
    url: str | None = None
    note: str | None = None


class EvidenceSource(BaseModel):
    source_type: str
    source_name: str
    title: str
    summary: str
    year: int | None = None
    url: str | None = None
    source_accessible: bool = True


class MCQOptionExplanation(BaseModel):
    option: str
    is_correct: bool = False
    explanation: str


class VerificationReport(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_grade: str = Field(pattern="^[ABC]$")
    recent_evidence_ratio: float
    authority_ratio: float
    anatomy_physiology_consistent: bool
    notes: list[str] = Field(default_factory=list)


class StructuredAnswer(BaseModel):
    question: str
    query_type: QueryType
    specialty: str | None = None
    pathophysiology: str
    clinical_features: str
    diagnosis: str
    treatment: str
    latest_evidence: str
    confidence_statement: str
    citations: list[Citation] = Field(default_factory=list)
    mcq_explanations: list[MCQOptionExplanation] = Field(default_factory=list)
    confidence: float = 0.0
    evidence_grade: str = "C"
    notes: list[str] = Field(default_factory=list)
