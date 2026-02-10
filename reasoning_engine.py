"""Minimal reasoning engine prototype.

Implements:
- input validation
- rule evaluation
- explanation output
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence


class ValidationError(ValueError):
    """Raised when engine input or rule definitions are invalid."""


@dataclass
class Rule:
    """A single rule evaluated by the reasoning engine.

    Attributes:
        id: Unique rule identifier.
        description: Human-readable purpose.
        condition: Callable that receives facts and returns True/False.
        outcome: Decision payload applied when condition is True.
    """

    id: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    outcome: Dict[str, Any]


@dataclass
class Explanation:
    """Detailed explanation of one rule evaluation."""

    rule_id: str
    description: str
    matched: bool
    outcome: Dict[str, Any] | None


@dataclass
class EvaluationResult:
    """Result for a full engine run."""

    matched_outcomes: List[Dict[str, Any]] = field(default_factory=list)
    explanation: List[Explanation] = field(default_factory=list)


def validate_facts(facts: Dict[str, Any], required_fields: Sequence[str]) -> None:
    """Validate incoming facts for rule evaluation."""

    if not isinstance(facts, dict):
        raise ValidationError("facts must be a dictionary")

    missing = [field for field in required_fields if field not in facts]
    if missing:
        raise ValidationError(f"missing required fact(s): {', '.join(missing)}")


def validate_rules(rules: Sequence[Rule]) -> None:
    """Validate rule collection structure."""

    if not isinstance(rules, Sequence) or not rules:
        raise ValidationError("rules must be a non-empty sequence")

    seen_ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, Rule):
            raise ValidationError("all rules must be Rule instances")
        if rule.id in seen_ids:
            raise ValidationError(f"duplicate rule id: {rule.id}")
        seen_ids.add(rule.id)


def evaluate_rules(facts: Dict[str, Any], rules: Sequence[Rule]) -> EvaluationResult:
    """Evaluate all rules and generate traceable explanation output."""

    validate_rules(rules)

    result = EvaluationResult()
    for rule in rules:
        matched = bool(rule.condition(facts))
        outcome = rule.outcome if matched else None

        if matched:
            result.matched_outcomes.append(rule.outcome)

        result.explanation.append(
            Explanation(
                rule_id=rule.id,
                description=rule.description,
                matched=matched,
                outcome=outcome,
            )
        )

    return result


def run_engine(
    facts: Dict[str, Any],
    rules: Sequence[Rule],
    required_fields: Sequence[str] = (),
) -> EvaluationResult:
    """Validate input and evaluate rules in one function call."""

    validate_facts(facts, required_fields)
    return evaluate_rules(facts, rules)


if __name__ == "__main__":
    # Tiny runnable demo.
    demo_rules = [
        Rule(
            id="r1",
            description="High blood pressure warning",
            condition=lambda f: f["systolic_bp"] >= 140,
            outcome={"alert": "possible_hypertension", "priority": "medium"},
        ),
        Rule(
            id="r2",
            description="Fever warning",
            condition=lambda f: f["temperature_c"] >= 38.0,
            outcome={"alert": "possible_fever", "priority": "low"},
        ),
    ]

    demo_facts = {"systolic_bp": 148, "temperature_c": 37.2}
    evaluation = run_engine(demo_facts, demo_rules, required_fields=["systolic_bp", "temperature_c"])

    print("Matched outcomes:", evaluation.matched_outcomes)
    print("Explanation:")
    for row in evaluation.explanation:
        print(vars(row))
