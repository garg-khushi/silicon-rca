from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def plot_severity_hist(out_dir: Path, incidents: pd.DataFrame) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "severity_hist.png"

    plt.figure()
    incidents["severity_score"].plot(kind="hist", bins=10)
    plt.title("Incident Severity Distribution")
    plt.xlabel("severity_score")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    return p


def plot_root_cause_bar(out_dir: Path, rca: pd.DataFrame) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "root_cause_counts.png"

    counts = rca["root_cause"].value_counts()
    plt.figure()
    counts.plot(kind="bar")
    plt.title("Root Cause Counts")
    plt.xlabel("root_cause")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    return p


def write_all_plots(out_dir: Path, incidents: pd.DataFrame, rca: pd.DataFrame):
    p1 = plot_severity_hist(out_dir, incidents)
    p2 = plot_root_cause_bar(out_dir, rca)
    return [p1, p2]
