import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from reasoning_engine import Rule, ValidationError, run_engine


def test_run_engine_matches_expected_rules():
    rules = [
        Rule(
            id="bp_high",
            description="Detect elevated blood pressure",
            condition=lambda f: f["bp"] >= 140,
            outcome={"alert": "high_bp"},
        ),
        Rule(
            id="age_risk",
            description="Detect age-based risk",
            condition=lambda f: f["age"] >= 65,
            outcome={"risk": "senior"},
        ),
    ]

    facts = {"bp": 145, "age": 50}
    result = run_engine(facts, rules, required_fields=["bp", "age"])

    assert result.matched_outcomes == [{"alert": "high_bp"}]
    assert len(result.explanation) == 2
    assert result.explanation[0].matched is True
    assert result.explanation[1].matched is False


def test_run_engine_missing_required_facts_raises_validation_error():
    rules = [
        Rule(
            id="simple",
            description="Simple rule",
            condition=lambda _: True,
            outcome={"ok": True},
        )
    ]

    with pytest.raises(ValidationError, match=r"missing required fact\(s\): age"):
        run_engine({"bp": 120}, rules, required_fields=["age"])
