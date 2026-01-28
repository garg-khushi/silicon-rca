from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np


METRICS = [
    "mem_latency_p99",
    "ecc_ce",
    "pcie_aer",
    "net_drops",
    "temp_c",
    "freq_ghz",
    "mem_bw",
    "cpu_util",
]


@dataclass
class Incident:
    incident_id: str
    host: str
    workload: str
    start_ts: pd.Timestamp
    end_ts: pd.Timestamp
    duration_sec: int
    top_signals: str
    event_hint: str
    severity_score: float

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["start_ts"] = str(self.start_ts)
        d["end_ts"] = str(self.end_ts)
        return d


def _robust_zscore(s: pd.Series) -> pd.Series:
    """
    Robust z-score using median and MAD.
    z = 0.6745*(x - median)/MAD
    """
    med = s.median()
    mad = (s - med).abs().median()
    if mad == 0:
        return pd.Series([0.0] * len(s), index=s.index)
    return 0.6745 * (s - med) / mad


def _build_anomaly_mask(dfh: pd.DataFrame) -> pd.DataFrame:
    """
    Compute robust z-score per metric per host and return a boolean mask dataframe.
    """
    z = pd.DataFrame(index=dfh.index)
    for m in METRICS:
        if m not in dfh.columns:
            continue
        z[m] = _robust_zscore(dfh[m].astype(float))
    # Rules: we treat high latency, ECC, PCIe, net drops, temp, mem_bw as "high-bad"
    # and freq as "low-bad" (throttling).
    high_bad = (
        (z["mem_latency_p99"] > 4.0)
        | (z["ecc_ce"] > 5.0)
        | (z["pcie_aer"] > 5.0)
        | (z["net_drops"] > 5.0)
        | (z["temp_c"] > 4.0)
        | (z["mem_bw"] > 4.0)
    )
    low_bad = (z["freq_ghz"] < -4.0)

    mask = pd.DataFrame(index=dfh.index)
    mask["is_anomaly"] = (high_bad | low_bad).fillna(False)
    # Keep z-scores for later attribution
    for m in z.columns:
        mask[f"z_{m}"] = z[m]
    return mask


def _coalesce_windows(timestamps: List[pd.Timestamp], max_gap_sec: int) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Merge anomaly points into windows if gaps <= max_gap_sec.
    """
    if not timestamps:
        return []
    timestamps = sorted(timestamps)
    windows = []
    start = timestamps[0]
    prev = timestamps[0]
    for ts in timestamps[1:]:
        if (ts - prev).total_seconds() <= max_gap_sec:
            prev = ts
        else:
            windows.append((start, prev))
            start = ts
            prev = ts
    windows.append((start, prev))
    return windows


def detect_incidents(
    df: pd.DataFrame,
    min_points: int = 10,
    max_gap_sec: int = 10,
) -> pd.DataFrame:
    """
    Detect incident windows per host using robust z-score + window coalescing.
    Returns a dataframe of incidents (one row per incident).
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values(["host", "timestamp"], inplace=True)

    incidents: List[Incident] = []
    inc_counter = 0

    for host, dfh in df.groupby("host", sort=False):
        mask = _build_anomaly_mask(dfh)
        dfh = dfh.join(mask)

        anomalous = dfh[dfh["is_anomaly"]]
        ts_list = anomalous["timestamp"].tolist()

        windows = _coalesce_windows(ts_list, max_gap_sec=max_gap_sec)

        for (start_ts, end_ts) in windows:
            window_df = dfh[(dfh["timestamp"] >= start_ts) & (dfh["timestamp"] <= end_ts)]
            if len(window_df) < min_points:
                continue
                        # Top signals with direction (important for correctness)
            z_cols = [c for c in window_df.columns if c.startswith("z_")]

            # Take the row where each z is maximal in absolute value, then keep signed value
            signed_peaks = {}
            for c in z_cols:
                idx = window_df[c].abs().idxmax()
                signed_peaks[c[2:]] = float(window_df.loc[idx, c])

            # Sort by absolute magnitude
            sorted_peaks = sorted(
                signed_peaks.items(),
                key=lambda kv: abs(kv[1]),
                reverse=True
            )

            top = []
            for k, v in sorted_peaks[:3]:
                sign = "+" if v >= 0 else "-"
                top.append(f"{k}:{sign}{abs(v):.1f}")
            top_signals = ",".join(top)
                        # Event hint (dominant non-NONE if present)
            event_hint = "NONE"
            non_none = window_df[window_df["event"] != "NONE"]["event"]
            if len(non_none) > 0:
                event_hint = non_none.value_counts().idxmax()

            # Severity score = sum of abs(top 3) (cap)
            severity = float(
                min(50.0, sum(abs(v) for _, v in sorted_peaks[:3]))
            )

            # # Top signals by absolute z-score peaks
            # z_cols = [c for c in window_df.columns if c.startswith("z_")]
            # peak = window_df[z_cols].abs().max().sort_values(ascending=False)

            # top = []
            # for c, v in peak.head(3).items():
            #     top.append(f"{c[2:]}:{v:.1f}")
            # top_signals = ",".join(top)

            # # Event hint (dominant non-NONE if present)
            # event_hint = "NONE"
            # non_none = window_df[window_df["event"] != "NONE"]["event"]
            # if len(non_none) > 0:
            #     event_hint = non_none.value_counts().idxmax()

            # # Severity score = sum of top 3 peak zscores (cap)
            # severity = float(min(50.0, peak.head(3).sum()))

            workload = window_df["workload"].mode().iloc[0] if "workload" in window_df.columns else "unknown"

            incidents.append(
                Incident(
                    incident_id=f"INC_{inc_counter:04d}",
                    host=host,
                    workload=workload,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    duration_sec=int((end_ts - start_ts).total_seconds()) + 1,
                    top_signals=top_signals,
                    event_hint=event_hint,
                    severity_score=severity,
                )
            )
            inc_counter += 1

    return pd.DataFrame([i.to_dict() for i in incidents]).sort_values(["severity_score"], ascending=False)
