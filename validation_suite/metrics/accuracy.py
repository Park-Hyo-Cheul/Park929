"""Accuracy and safety metrics for implant validation."""

from __future__ import annotations

import math
from typing import Any


def compute_implant_deviation(plan: Any, ground_truth: Any) -> float:
    """Compute RMSE deviation between planned and ground-truth implant centroids."""

    if not isinstance(plan, list) or not isinstance(ground_truth, list):
        return 0.0

    if not plan or not ground_truth:
        return 0.0

    count = min(len(plan), len(ground_truth))
    if count == 0:
        return 0.0

    error_sum = 0.0
    for idx in range(count):
        p = plan[idx]
        g = ground_truth[idx]

        px, py, pz = float(p.get("x", 0.0)), float(p.get("y", 0.0)), float(p.get("z", 0.0))
        gx, gy, gz = float(g.get("x", 0.0)), float(g.get("y", 0.0)), float(g.get("z", 0.0))

        squared_distance = (px - gx) ** 2 + (py - gy) ** 2 + (pz - gz) ** 2
        error_sum += squared_distance

    return math.sqrt(error_sum / count)


def compute_safety_margin(min_distance: float) -> dict[str, float | bool]:
    """Return safety margin details given minimum canal distance."""

    distance = float(min_distance)
    return {
        "min_distance": distance,
        "safety_margin": max(distance - 2.0, 0.0),
        "is_safe": distance >= 2.0,
    }
