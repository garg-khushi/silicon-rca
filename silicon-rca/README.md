# Silicon-RCA — Post-Silicon Incident Detection & Root-Cause Analytics (Fleet Telemetry)

A production-style, explainable debugging pipeline inspired by data-center silicon enablement workflows.
It ingests **dense performance counters** + **sparse silicon event logs**, correlates them in time, detects **incident windows**, and produces **ranked root-cause hypotheses** with auditable evidence and recommended next actions.

> Designed to demonstrate: post-silicon validation + bring-up thinking, fleet analytics, debug tooling, and lifecycle demonstrated via a clean CLI and reproducible artifacts.

---

## What it does (end-to-end)

**Input**
- `counters.csv` — time-series counters (CPU/memory/PCIe/network/thermal)
- `logs.jsonl` — structured silicon events (ECC bursts, PCIe AER, thermal events, congestion)

**Pipeline**
1. **Ingest**: parse/normalize timestamps
2. **Correlate**: join logs↔counters via time buckets
3. **Detect incidents**: robust (MAD) z-score anomalies → coalesced time windows
4. **RCA**: explainable rule-based ranking → confidence + evidence trace
5. **Report**: markdown report + plots

**Output artifacts**
- `out/incidents.csv` — incident windows + severity + directional top signals
- `out/rca_results.csv` — root-cause + confidence + rule hits + recommendations
- `out/report.md` — executive report (top incidents + RCA summary)
- `out/severity_hist.png` — severity distribution
- `out/root_cause_counts.png` — root cause frequency

---

## Quickstart (one command)

### 1) Install (editable)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
