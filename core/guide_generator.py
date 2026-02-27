"""Robust guide generator primitives.

This module keeps boolean operations failure-safe and provides fallback behavior
for manufacturing-oriented pipelines.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.mesh_preprocess import preprocess_for_boolean

logger = logging.getLogger(__name__)

try:
    import vtk  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    vtk = None


FAILURE_LOG_DIR = Path("logs/guide_failures")


def _safe_set_input_data(alg: Any, polydata: Any, idx: int | None = None) -> None:
    if idx is not None and hasattr(alg, "SetInputData"):
        alg.SetInputData(idx, polydata)
    elif hasattr(alg, "SetInputData"):
        alg.SetInputData(polydata)
    elif idx is not None and hasattr(alg, "SetInputDataObject"):
        alg.SetInputDataObject(idx, polydata)
    elif hasattr(alg, "SetInputDataObject"):
        alg.SetInputDataObject(polydata)


def _is_non_empty_polydata(polydata: Any) -> bool:
    return bool(polydata is not None and hasattr(polydata, "GetNumberOfPoints") and polydata.GetNumberOfPoints() > 0)


def _serialize_polydata(polydata: Any, path: Path) -> str | None:
    if vtk is None or polydata is None:
        return None
    try:
        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetFileName(str(path))
        _safe_set_input_data(writer, polydata)
        writer.Write()
        return str(path)
    except Exception:
        return None


def _save_failure_bundle(base: Any, subtract: Any, params: dict[str, Any], reason: str) -> dict[str, str]:
    FAILURE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = FAILURE_LOG_DIR / f"failure_{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}

    base_file = _serialize_polydata(base, bundle_dir / "base.vtp")
    subtract_file = _serialize_polydata(subtract, bundle_dir / "subtract.vtp")
    if base_file:
        artifacts["base_mesh"] = base_file
    if subtract_file:
        artifacts["subtract_mesh"] = subtract_file

    params_path = bundle_dir / "params.json"
    params_path.write_text(json.dumps(params, indent=2), encoding="utf-8")
    artifacts["params"] = str(params_path)

    snapshot_path = bundle_dir / "snapshot.log"
    snapshot_path.write_text(reason, encoding="utf-8")
    artifacts["snapshot"] = str(snapshot_path)

    return artifacts


def _attempt_boolean_difference(base: Any, subtract: Any) -> Any:
    if vtk is None:
        return None

    boolean_filter = vtk.vtkBooleanOperationPolyDataFilter()
    boolean_filter.SetOperationToDifference()
    _safe_set_input_data(boolean_filter, base, 0)
    _safe_set_input_data(boolean_filter, subtract, 1)
    boolean_filter.Update()
    output = boolean_filter.GetOutput()

    return output if _is_non_empty_polydata(output) else None


def robust_boolean_difference(base: Any, subtract: Any) -> dict[str, Any]:
    """Perform a crash-safe boolean difference with fallback behavior."""

    debug_parts: dict[str, Any] = {
        "preprocessed": False,
        "attempts": [],
        "failure_artifacts": {},
        "fallback_mode": None,
    }

    if base is None or subtract is None:
        reason = "Input mesh missing for boolean difference."
        logger.error(reason)
        return {
            "guide_polydata": None,
            "debug_parts": {**debug_parts, "reason": reason},
            "status": "failed",
        }

    try:
        base_pp = preprocess_for_boolean(base)
        subtract_pp = preprocess_for_boolean(subtract)
        debug_parts["preprocessed"] = True
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Preprocessing failed, using raw meshes: %s", exc)
        base_pp = base
        subtract_pp = subtract

    try:
        result = _attempt_boolean_difference(base_pp, subtract_pp)
        debug_parts["attempts"].append("base-minus-subtract")
        if _is_non_empty_polydata(result):
            return {"guide_polydata": result, "debug_parts": debug_parts, "status": "success"}
    except Exception as exc:
        logger.warning("Boolean difference failed in primary order: %s", exc)

    try:
        result = _attempt_boolean_difference(subtract_pp, base_pp)
        debug_parts["attempts"].append("subtract-minus-base")
        if _is_non_empty_polydata(result):
            return {"guide_polydata": result, "debug_parts": debug_parts, "status": "success"}
    except Exception as exc:
        logger.warning("Boolean difference failed in alternate order: %s", exc)

    reason = "Boolean operation failed in both operand orders; channel-only fallback activated."
    debug_parts["fallback_mode"] = "channel_only"
    debug_parts["failure_artifacts"] = _save_failure_bundle(
        base_pp,
        subtract_pp,
        params={"strategy": "channel-only", "attempts": debug_parts["attempts"]},
        reason=reason,
    )
    logger.error(reason)

    return {
        "guide_polydata": base_pp,
        "debug_parts": debug_parts,
        "status": "fallback",
    }
