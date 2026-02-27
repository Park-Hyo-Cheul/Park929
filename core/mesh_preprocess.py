"""Mesh preprocessing utilities for robust boolean operations.

The helpers in this module are intentionally defensive: all operations fail soft
and return a best-effort mesh instead of raising runtime exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MeshQC:
    """Small quality-control summary for a mesh."""

    watertight: bool
    self_intersections: bool


try:
    import vtk  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    vtk = None


try:
    import trimesh  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    trimesh = None


def _safe_set_input_data(alg: Any, polydata: Any) -> None:
    if hasattr(alg, "SetInputData"):
        alg.SetInputData(polydata)
    elif hasattr(alg, "SetInputDataObject"):
        alg.SetInputDataObject(polydata)


def _run_vtk_filter(polydata: Any, flt: Any) -> Any:
    _safe_set_input_data(flt, polydata)
    flt.Update()
    return flt.GetOutput()


def preprocess_for_boolean(polydata: Any) -> Any:
    """Prepare a mesh for more stable boolean operations.

    Steps:
    1. triangulate
    2. clean (remove duplicate points)
    3. fill small holes
    4. recalc normals
    5. connectivity filter (largest region)
    6. optional decimation (light)

    Returns:
        Best-effort processed mesh. If VTK is unavailable, returns the original
        mesh untouched.
    """

    if polydata is None or vtk is None:
        return polydata

    output = polydata

    try:
        output = _run_vtk_filter(output, vtk.vtkTriangleFilter())
    except Exception:
        pass

    try:
        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetToleranceIsAbsolute(False)
        cleaner.ConvertLinesToPointsOff()
        output = _run_vtk_filter(output, cleaner)
    except Exception:
        pass

    try:
        holes = vtk.vtkFillHolesFilter()
        holes.SetHoleSize(2.0)
        output = _run_vtk_filter(output, holes)
    except Exception:
        pass

    try:
        normals = vtk.vtkPolyDataNormals()
        normals.AutoOrientNormalsOn()
        normals.ConsistencyOn()
        normals.SplittingOff()
        output = _run_vtk_filter(output, normals)
    except Exception:
        pass

    try:
        conn = vtk.vtkConnectivityFilter()
        _safe_set_input_data(conn, output)
        conn.SetExtractionModeToLargestRegion()
        conn.Update()
        geom = vtk.vtkGeometryFilter()
        _safe_set_input_data(geom, conn.GetOutput())
        geom.Update()
        output = geom.GetOutput()
    except Exception:
        pass

    try:
        decimate = vtk.vtkDecimatePro()
        _safe_set_input_data(decimate, output)
        decimate.SetTargetReduction(0.10)
        decimate.PreserveTopologyOn()
        decimate.BoundaryVertexDeletionOff()
        decimate.Update()
        output = decimate.GetOutput()
    except Exception:
        pass

    return output


def is_watertight(polydata: Any) -> bool:
    """Check if a mesh appears watertight."""

    if polydata is None:
        return False

    if vtk is not None:
        try:
            edges = vtk.vtkFeatureEdges()
            _safe_set_input_data(edges, polydata)
            edges.BoundaryEdgesOn()
            edges.NonManifoldEdgesOn()
            edges.ManifoldEdgesOff()
            edges.FeatureEdgesOff()
            edges.Update()
            return edges.GetOutput().GetNumberOfCells() == 0
        except Exception:
            pass

    if trimesh is not None:
        try:
            mesh = trimesh.Trimesh(
                vertices=[polydata.GetPoint(i) for i in range(polydata.GetNumberOfPoints())],
                faces=[],
                process=False,
            )
            return bool(mesh.is_watertight)
        except Exception:
            return False

    return False


def detect_self_intersections(polydata: Any) -> bool:
    """Detect mesh self-intersections where tool support exists."""

    if polydata is None:
        return False

    if trimesh is not None:
        try:
            mesh = trimesh.Trimesh(
                vertices=[polydata.GetPoint(i) for i in range(polydata.GetNumberOfPoints())],
                faces=[],
                process=False,
            )
            intersector = trimesh.intersections.mesh_self_intersection(mesh)
            return len(intersector) > 0
        except Exception:
            return False

    return False
