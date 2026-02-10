from cdss.medqna.query_router import route_query
from cdss.medqna.schemas import QueryType


def test_route_query_mcq_by_flag():
    assert route_query("Which is best?", mcq_mode=True) == QueryType.MCQ


def test_route_query_mcq_by_choices():
    assert route_query("Choose one", choices=["A", "B"]) == QueryType.MCQ


def test_route_query_drug_comparison():
    assert route_query("Compare insulin vs metformin drug efficacy") == QueryType.DRUG_COMPARISON


def test_route_query_general():
    assert route_query("What are features of COPD?") == QueryType.GENERAL
