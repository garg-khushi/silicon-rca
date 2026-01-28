from __future__ import annotations

from pathlib import Path
import pandas as pd


def write_markdown_report(
    out_dir: Path,
    incidents: pd.DataFrame,
    rca: pd.DataFrame,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.md"

    # Summary tables
    top_inc = incidents.sort_values("severity_score", ascending=False).head(10)
    rc_dist = rca["root_cause"].value_counts().reset_index()
    rc_dist.columns = ["root_cause", "count"]

    lines = []
    lines.append("# Post-Silicon Failure RCA Report\n")
    lines.append("## Executive Summary\n")
    lines.append(f"- Total incidents detected: **{len(incidents)}**\n")
    lines.append("- Top root-cause categories:\n")

    for _, row in rc_dist.head(5).iterrows():
        lines.append(f"  - **{row['root_cause']}**: {int(row['count'])}\n")

    lines.append("\n## Top Incidents (by severity)\n")
    lines.append(top_inc[["incident_id", "host", "workload", "event_hint", "severity_score", "top_signals"]]
                 .to_markdown(index=False))
    lines.append("\n## RCA Results (Top 10)\n")

    joined = pd.merge(top_inc, rca, on="incident_id", how="left")
    lines.append(
        joined[["incident_id", "root_cause", "confidence", "explanation"]].to_markdown(index=False)
    )

    lines.append("\n## Recommended Next Actions\n")
    for _, row in joined.iterrows():
        lines.append(f"### {row['incident_id']} — {row['root_cause']} (conf {row['confidence']:.2f})\n")
        lines.append(f"- **Why:** {row['explanation']}\n")
        lines.append(f"- **Validation:** {row['recommended_validation']}\n")
        lines.append(f"- **Mitigation:** {row['recommended_mitigation']}\n")

    report_path.write_text("\n".join(lines))
    return report_path
