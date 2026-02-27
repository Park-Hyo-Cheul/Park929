"""HTML reporting helpers for guide generation outputs."""

from __future__ import annotations

from html import escape
from typing import Any


def _bool_label(value: bool) -> str:
    return "PASS" if value else "FAIL"


def render_guide_validation_report(
    patient_id: str,
    thickness_stats: dict[str, Any],
    boolean_status: str,
    qc_flags: dict[str, bool],
    printable_confidence: float,
) -> str:
    """Render a compact validation report for guide manufacturing readiness."""

    rows = "".join(
        f"<tr><td>{escape(key)}</td><td>{_bool_label(bool(val))}</td></tr>"
        for key, val in qc_flags.items()
    )

    html = f"""
    <html>
      <head>
        <title>Guide Validation Report</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 1.2rem; }}
          table {{ border-collapse: collapse; width: 100%; }}
          td, th {{ border: 1px solid #ccc; padding: 0.4rem; text-align: left; }}
          .ok {{ color: #0b7a0b; }}
          .warn {{ color: #b15d00; }}
        </style>
      </head>
      <body>
        <h1>Guide Validation Report</h1>
        <p><strong>Patient:</strong> {escape(patient_id)}</p>
        <p><strong>Boolean status:</strong> {escape(boolean_status)}</p>

        <h2>Thickness Map Statistics</h2>
        <ul>
          <li>Minimum thickness (mm): {escape(str(thickness_stats.get('minimum')))}</li>
          <li>Mean thickness (mm): {escape(str(thickness_stats.get('mean')))}</li>
          <li>Max thickness (mm): {escape(str(thickness_stats.get('maximum')))}</li>
        </ul>

        <h2>QC Pass/Fail Flags</h2>
        <table>
          <thead><tr><th>Check</th><th>Status</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>

        <h2>Printable Confidence Score</h2>
        <p class=\"{'ok' if printable_confidence >= 0.6 else 'warn'}\">{printable_confidence:.3f}</p>
      </body>
    </html>
    """
    return html.strip()
