from pathlib import Path
import json
import pandas as pd


def load_counters(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df.sort_values(["host", "timestamp"], inplace=True)
    return df


def load_logs(path: Path) -> pd.DataFrame:
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values(["host", "timestamp"], inplace=True)
    return df


def load_fleet_data(data_dir: Path):
    counters = load_counters(data_dir / "counters.csv")
    logs = load_logs(data_dir / "logs.jsonl")
    return counters, logs
