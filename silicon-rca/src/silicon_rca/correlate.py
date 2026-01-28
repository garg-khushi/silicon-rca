import pandas as pd


def correlate_logs_to_counters(
    counters: pd.DataFrame,
    logs: pd.DataFrame,
    window_sec: int = 5,
) -> pd.DataFrame:
    """
    Align log events to nearest counter samples within a time window.
    """

    counters = counters.copy()
    logs = logs.copy()

    counters["ts_bucket"] = counters["timestamp"].dt.floor(f"{window_sec}s")
    logs["ts_bucket"] = logs["timestamp"].dt.floor(f"{window_sec}s")

    merged = pd.merge(
        counters,
        logs,
        on=["host", "ts_bucket"],
        how="left",
        suffixes=("", "_log"),
    )

    merged["event"] = merged["event"].fillna("NONE")
    merged["severity"] = merged["severity"].fillna("NONE")

    return merged.drop(columns=["ts_bucket"])
