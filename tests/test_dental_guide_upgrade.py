from __future__ import annotations

import subprocess
from pathlib import Path

from core.guide_generator import robust_boolean_difference
from core.manufacturing_qc import qc_summary
from reporting.report_html import render_guide_validation_report


def test_robust_boolean_difference_never_crashes_with_generic_inputs():
    result = robust_boolean_difference({"mesh": "a"}, {"mesh": "b"})
    assert result["status"] in {"success", "fallback", "failed"}
    assert "debug_parts" in result


def test_qc_summary_has_required_sections():
    qc = qc_summary({"mock": "poly"}, implants=[{"position": [0, 0, 0]}, {"position": [6, 0, 0]}])
    assert set(qc).issuperset({"minimum_thickness", "sleeve_collision", "undercut", "printable_orientation", "passes"})


def test_report_html_contains_new_sections():
    html = render_guide_validation_report(
        patient_id="P-001",
        thickness_stats={"minimum": 1.7, "mean": 2.3, "maximum": 4.2},
        boolean_status="fallback",
        qc_flags={"minimum_thickness": True, "sleeve_collision": False},
        printable_confidence=0.74,
    )
    assert "Thickness Map Statistics" in html
    assert "Boolean status" in html
    assert "Printable Confidence Score" in html


def test_stress_cli_exists_and_runs_help():
    path = Path("dental-guide")
    assert path.exists()
    completed = subprocess.run([f"./{path}", "--help"], check=False, capture_output=True, text=True)
    assert completed.returncode == 0
    assert "--stress-test" in completed.stdout
