"""Validation thresholds and report defaults for dental-guide."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationThresholds:
    """Acceptance criteria for validation runs."""

    max_rmse: float = 1.5
    min_canal_distance: float = 2.0
    min_guide_success_rate: float = 0.95


THRESHOLDS = ValidationThresholds()
