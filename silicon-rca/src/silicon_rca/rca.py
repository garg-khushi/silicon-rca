from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
import pandas as pd


@dataclass
class RCAResult:
    incident_id: str
    root_cause: str
    confidence: float
    explanation: str
    evidence_top_signals: str
    rule_hits: str
    confidence_rationale: str
    recommended_validation: str
    recommended_mitigation: str


    def to_dict(self) -> Dict:
        return asdict(self)


def _parse_top_signals(top_signals: str) -> Dict[str, float]:
    """
    "mem_latency_p99:7.2,ecc_ce:9.1,mem_bw:5.3" -> dict
    """
    d: Dict[str, float] = {}
    if not isinstance(top_signals, str):
        return d
    for part in top_signals.split(","):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        try:
            d[k.strip()] = float(v.replace("+", ""))
        except ValueError:
            continue
    return d


def rank_root_cause(incident_row: pd.Series) -> RCAResult:
    """
    Explainable rule-based RCA.
    Uses incident top_signals + event_hint + workload.
    """
    incident_id = incident_row["incident_id"]
    workload = incident_row.get("workload", "unknown")
    event_hint = incident_row.get("event_hint", "NONE")
    signals = _parse_top_signals(incident_row.get("top_signals", ""))
    rule_hits = []

    # Helper flags
    ecc = signals.get("ecc_ce", 0.0)
    lat = signals.get("mem_latency_p99", 0.0)
    bw = signals.get("mem_bw", 0.0)
    temp = signals.get("temp_c", 0.0)
    freq = signals.get("freq_ghz", 0.0)
    pcie = signals.get("pcie_aer", 0.0)
    net = signals.get("net_drops", 0.0)
    cpu = signals.get("cpu_util", 0.0)

    # Candidate scoring (simple, explainable)
    candidates: List[Tuple[str, float, str]] = []

    # DRAM/ECC / memory subsystem
    score_mem = 0.0
    score_mem += 0.6 * (ecc > 4.0)
    score_mem += 0.5 * (lat > 4.0)
    score_mem += 0.3 * (bw > 4.0)
    score_mem += 0.2 * (workload in ["ai_train", "video_transcode"])
    score_mem += 0.4 * (event_hint == "DRAM_ECC")
    if event_hint == "DRAM_ECC":
        rule_hits.append("event_hint=DRAM_ECC")
    if ecc > 4.0:
        rule_hits.append("ecc_ce_high")
    if lat > 4.0:
        rule_hits.append("mem_latency_p99_high")

    candidates.append((
        "DRAM/ECC or memory-controller stress",
        score_mem,
        "ECC bursts + tail latency + high bandwidth suggest memory subsystem stress"
    ))

    # PCIe link instability
    score_pcie = 0.0
    score_pcie += 0.7 * (pcie > 4.0)
    score_pcie += 0.3 * (workload in ["ai_train", "video_transcode"])
    score_pcie += 0.5 * (event_hint == "PCIE_AER")
    if event_hint == "PCIE_AER":
        rule_hits.append("event_hint=PCIE_AER")
    if pcie > 4.0:
        rule_hits.append("pcie_aer_high")

    candidates.append((
        "PCIe link instability / AER storm",
        score_pcie,
        "Elevated PCIe AER indicates link errors, retries, or device reset behavior"
    ))

    # Thermal throttling / power management
    score_thermal = 0.0
    score_thermal += 0.6 * (temp > 4.0)
    score_thermal += 0.6 * (freq > 4.0)  # NOTE: freq_ghz z-score is negative for low-bad, but peak abs used earlier.
    score_thermal += 0.2 * (cpu > 4.0)
    score_thermal += 0.4 * (event_hint == "THERMAL")
    if event_hint == "THERMAL":
        rule_hits.append("event_hint=THERMAL")
    if temp > 4.0:
        rule_hits.append("temp_high")
    if "freq_ghz" in signals and signals["freq_ghz"] < -4.0:
        rule_hits.append("freq_drop")

    candidates.append((
        "Thermal throttling / power management",
        score_thermal,
        "Thermal excursion and frequency drop patterns suggest throttling"
    ))

    # Network congestion / queue saturation
    score_net = 0.0
    score_net += 0.7 * (net > 4.0)
    score_net += 0.4 * (workload == "network_burst")
    score_net += 0.5 * (event_hint == "NETWORK_CONGESTION")
    if event_hint == "NETWORK_CONGESTION":
        rule_hits.append("event_hint=NETWORK_CONGESTION")
    if net > 4.0:
        rule_hits.append("net_drops_high")

    candidates.append((
        "Network congestion / queue saturation",
        score_net,
        "Drops + bursty networking workload indicates congestion or queue saturation"
    ))

    # Pick best
    candidates.sort(key=lambda x: x[1], reverse=True)
    best_cause, best_score, best_expl = candidates[0]

    # Convert score to confidence (bounded)
    confidence = min(0.95, max(0.30, 0.30 + best_score * 0.20))
    confidence_rationale = f"confidence=0.30+0.20*score(best={best_score:.2f}) capped to [0.30,0.95]"

    # Recommendations (validation + mitigation) per root cause
    if "DRAM/ECC" in best_cause:
        validation = (
            "Reproduce under ai_train/video_transcode with sustained memory bandwidth; "
            "collect ECC counters, mem latency histograms, bandwidth, and error addresses if available."
        )
        mitigation = (
            "Check ECC thresholding, memory timing margins, and firmware; "
            "add regression test for ECC burst + latency spike signature."
        )
    elif "PCIe" in best_cause:
        validation = (
            "Run PCIe stress (high I/O, retries) and capture AER logs, link retrain counts, "
            "and device reset events; compare across firmware versions."
        )
        mitigation = (
            "Tune retry/timeout policies, verify link training stability, "
            "add regression for AER storm signature and alerting thresholds."
        )
    elif "Thermal" in best_cause:
        validation = (
            "Run sustained compute load; record temp, freq, perf counters; "
            "verify throttling triggers and thermal headroom across racks."
        )
        mitigation = (
            "Improve thermal policy/limits, ensure cooling and fan curves; "
            "add regression for perf drop under thermal excursion signature."
        )
    else:
        validation = (
            "Generate bursty traffic; collect drops, queue depth (if modeled), retransmits; "
            "verify congestion control behavior under peak load."
        )
        mitigation = (
            "Tune queue thresholds and traffic shaping; "
            "add regression test for drop spikes under network burst signature."
        )

    return RCAResult(
        incident_id=str(incident_id),
        root_cause=best_cause,
        confidence=float(confidence),
        explanation=best_expl,
        evidence_top_signals=str(incident_row.get("top_signals", "")),
        rule_hits=";".join(sorted(set(rule_hits))),
        confidence_rationale=confidence_rationale,
        recommended_validation=validation,
        recommended_mitigation=mitigation,
    )

    


def run_rca(incidents_df: pd.DataFrame) -> pd.DataFrame:
    results = [rank_root_cause(row).to_dict() for _, row in incidents_df.iterrows()]
    return pd.DataFrame(results)
