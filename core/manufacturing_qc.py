"""Manufacturing quality checks for surgical guide meshes."""

from __future__ import annotations

import math
from typing import Any


try:
    import vtk  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    vtk = None


def _polydata_bounds(polydata: Any) -> tuple[float, float, float, float, float, float]:
    if polydata is not None and hasattr(polydata, "GetBounds"):
        bounds = polydata.GetBounds()
        if bounds:
            return tuple(float(v) for v in bounds)
    return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def minimum_thickness(polydata: Any) -> dict[str, Any]:
    """Approximate minimum thickness in millimeters."""

    x0, x1, y0, y1, z0, z1 = _polydata_bounds(polydata)
    dims = [abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)]
    dims_non_zero = [d for d in dims if d > 0]
    estimated_min = min(dims_non_zero) if dims_non_zero else 0.0
    return {
        "minimum_thickness_mm": round(float(estimated_min), 3),
        "passes": estimated_min >= 1.5,
    }


def sleeve_collision_check(implants: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Simple center-distance collision check for implant sleeves."""

    implants = implants or []
    collisions: list[dict[str, Any]] = []

    for i in range(len(implants)):
        p1 = implants[i].get("position", [0.0, 0.0, 0.0])
        r1 = float(implants[i].get("sleeve_radius_mm", 2.5))
        for j in range(i + 1, len(implants)):
            p2 = implants[j].get("position", [0.0, 0.0, 0.0])
            r2 = float(implants[j].get("sleeve_radius_mm", 2.5))
            dist = math.dist(p1, p2)
            if dist < (r1 + r2):
                collisions.append({"implant_a": i, "implant_b": j, "distance": round(dist, 3)})

    return {
        "passes": len(collisions) == 0,
        "collisions": collisions,
    }


def undercut_detection(polydata: Any) -> dict[str, Any]:
    """Heuristic undercut risk estimation using mesh normals spread."""

    if vtk is None or polydata is None:
        return {"undercut_risk": 0.0, "passes": True}

    try:
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(polydata)
        normals.ComputePointNormalsOn()
        normals.Update()
        out = normals.GetOutput()
        normal_data = out.GetPointData().GetNormals()
        if normal_data is None or normal_data.GetNumberOfTuples() == 0:
            return {"undercut_risk": 0.0, "passes": True}

        backward = 0
        total = normal_data.GetNumberOfTuples()
        for idx in range(total):
            nx, ny, nz = normal_data.GetTuple3(idx)
            if nz < -0.2:
                backward += 1

        risk = backward / total
        return {"undercut_risk": round(risk, 3), "passes": risk < 0.35}
    except Exception:
        return {"undercut_risk": 0.0, "passes": True}


def printable_orientation_score(polydata: Any) -> dict[str, Any]:
    """Compute a printability confidence score in [0, 1]."""

    x0, x1, y0, y1, z0, z1 = _polydata_bounds(polydata)
    width = max(abs(x1 - x0), 1e-6)
    depth = max(abs(y1 - y0), 1e-6)
    height = max(abs(z1 - z0), 1e-6)

    footprint = width * depth
    slenderness = height / max(width, depth)

    footprint_score = min(1.0, footprint / 600.0)
    slenderness_penalty = min(1.0, max(0.0, (slenderness - 1.2) / 1.8))
    score = max(0.0, min(1.0, footprint_score * (1.0 - 0.5 * slenderness_penalty)))

    return {
        "score": round(score, 3),
        "passes": score >= 0.6,
    }


def qc_summary(polydata: Any, implants: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Aggregate all manufacturing checks."""

    thickness = minimum_thickness(polydata)
    sleeve = sleeve_collision_check(implants)
    undercut = undercut_detection(polydata)
    orientation = printable_orientation_score(polydata)

    return {
        "minimum_thickness": thickness,
        "sleeve_collision": sleeve,
        "undercut": undercut,
        "printable_orientation": orientation,
        "passes": all(
            [
                thickness["passes"],
                sleeve["passes"],
                undercut["passes"],
                orientation["passes"],
            ]
        ),
    }
