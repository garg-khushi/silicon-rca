from __future__ import annotations

from pathlib import Path
import time

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from silicon_rca.ingest import load_fleet_data
from silicon_rca.correlate import correlate_logs_to_counters
from silicon_rca.detect import detect_incidents
from silicon_rca.rca import run_rca
from silicon_rca.report import write_markdown_report
from silicon_rca.plots import write_all_plots

app = typer.Typer(add_completion=False)
console = Console()

@app.callback()
def main_callback():
    """
    Silicon RCA CLI.
    """
    pass

def _print_top_incidents(inc: pd.DataFrame, n: int = 8) -> None:
    if len(inc) == 0:
        console.print("[yellow]No incidents detected.[/yellow]")
        return

    top = inc.sort_values("severity_score", ascending=False).head(n)
    t = Table(title=f"Top {min(n, len(top))} Incidents")
    for col in ["incident_id", "host", "workload", "event_hint", "severity_score", "top_signals"]:
        t.add_column(col)
    for _, r in top.iterrows():
        t.add_row(
            str(r["incident_id"]),
            str(r["host"]),
            str(r["workload"]),
            str(r["event_hint"]),
            f"{float(r['severity_score']):.2f}",
            str(r["top_signals"]),
        )
    console.print(t)


@app.command()
def run(
    data: Path = typer.Option(Path("data/demo_fleet"), help="Input folder with counters.csv and logs.jsonl"),
    out: Path = typer.Option(Path("out"), help="Output folder for incidents/RCA/report/plots"),
    window_sec: int = typer.Option(5, help="Time-bucket window for log↔counter correlation"),
    min_points: int = typer.Option(8, help="Minimum points in an incident window"),
    max_gap_sec: int = typer.Option(10, help="Max allowed gap (sec) inside an incident window"),
):
    """Run end-to-end pipeline: ingest → correlate → detect → RCA → report → plots."""
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Input:[/bold] {data}")
    console.print(f"[bold]Output:[/bold] {out}\n")

    counters, logs = load_fleet_data(data)
    df = correlate_logs_to_counters(counters, logs, window_sec=window_sec)

    inc = detect_incidents(df, min_points=min_points, max_gap_sec=max_gap_sec)
    inc_path = out / "incidents.csv"
    inc.to_csv(inc_path, index=False)

    rca = run_rca(inc)
    rca_path = out / "rca_results.csv"
    rca.to_csv(rca_path, index=False)

    report_path = write_markdown_report(out, inc, rca)
    plot_paths = write_all_plots(out, inc, rca)

    console.print("[green]Artifacts written:[/green]")
    console.print(f" - {inc_path}")
    console.print(f" - {rca_path}")
    console.print(f" - {report_path}")
    for p in plot_paths:
        console.print(f" - {p}")

    console.print()
    _print_top_incidents(inc, n=8)
    console.print(f"\n[bold green]Done[/bold green] in {time.time() - t0:.2f}s")


def main():
    app()


if __name__ == "__main__":
    main()
