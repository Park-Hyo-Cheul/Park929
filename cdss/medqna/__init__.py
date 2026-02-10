"""Medicine for Physicians Q&A layer."""

from .composer import compose_answer
from .query_router import route_query
from .retriever import retrieve_evidence
from .schemas import StructuredAnswer

__all__ = ["compose_answer", "route_query", "retrieve_evidence", "StructuredAnswer"]
