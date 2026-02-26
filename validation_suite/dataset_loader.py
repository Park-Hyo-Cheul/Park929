"""Dataset loading helpers for clinical validation cases."""

from __future__ import annotations

import json
from pathlib import Path


def _first_existing(case_dir: Path, patterns: list[str]) -> str | None:
    for pattern in patterns:
        matches = sorted(case_dir.glob(pattern))
        if matches:
            return str(matches[0])
    return None


def _load_ground_truth(path: Path) -> list[dict]:
    if not path.exists():
        return []

    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            implants = payload.get("implants")
            if isinstance(implants, list):
                return implants
    return []


def load_case(case_dir: str) -> dict:
    """Load one validation case directory into a standard dictionary."""

    case_path = Path(case_dir)
    if not case_path.exists() or not case_path.is_dir():
        raise FileNotFoundError(f"Case directory not found: {case_dir}")

    cbct_dir = case_path / "cbct"
    if not cbct_dir.exists():
        cbct_dir = case_path

    ios_path = _first_existing(case_path, ["*ios*.stl", "*IOS*.stl", "*.stl", "*.ply"])
    canal_path = _first_existing(case_path, ["*canal*.json", "*canal*.nii*", "*canal*.csv"])

    gt_json = case_path / "ground_truth_implants.json"
    if not gt_json.exists():
        gt_json = case_path / "ground_truth.json"

    return {
        "case_id": case_path.name,
        "cbct_dir": str(cbct_dir),
        "ios_path": ios_path,
        "canal_path": canal_path,
        "ground_truth_implants": _load_ground_truth(gt_json),
    }
