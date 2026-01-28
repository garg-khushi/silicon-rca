# silicon-rca

Post-silicon failure analytics and explainable root-cause analysis framework for data‑center silicon. **silicon-rca** ingests fleet-style telemetry (time-series counters and structured silicon events), detects incident windows using robust statistics, and produces human-readable RCA reports with confidence, evidence, and recommended validation and mitigation actions.

***

## Overview

Modern data-center silicon often fails intermittently, under specific workloads, with noisy counters and partial logs rather than clean, repeatable testcases. **silicon-rca** is a small but realistic post-silicon debug tool inspired by internal fleet enablement workflows at large hyperscalers.

The framework focuses on:

- Fleet-level telemetry across multiple hosts and workloads, not single-device toy examples.  
- Workload-triggered failures (for example `ai_train`, `video_transcode`, `network_burst`), not synthetic random faults.  
- Explainable root-cause analysis that tells you what failed, why it failed, and what to do next.

***

## Core capabilities

### Silicon lifecycle aware

The project is built around **silicon** lifecycle thinking: deployment → production behavior → failure → remediation → feedback into validation.

- Models multiple hosts with workload labels and realistic stress patterns.  
- Treats telemetry as workload-dependent, not as static lab counters.  
- Answers questions like "what fails in production when this workload runs?" instead of "did any counter spike?".

### Troubleshooting, debug & analytics

The pipeline implements an end‑to‑end debug flow:

1. Ingest raw telemetry (counters and event logs).  
2. Normalize and correlate signals across hosts and time buckets.  
3. Detect **incident windows** using MAD-based z‑scores instead of naive thresholds (more realistic for noisy, heavy‑tailed telemetry).  
4. Preserve directional evidence (for example `freq_ghz: -4.4`, `temp_c: +4.6`) to distinguish throttling from pure thermal excursions.

Each incident produces:

- Ranked root‑cause hypothesis.  
- Confidence and rule hits.  
- Evidence trace showing which signals moved, by how much, and under which workload.  
- Suggested validation and mitigation steps.

The goal is not just anomaly detection, but **debuggable** explanations that match how real silicon teams reason about failures.

***

## Hardware domains modeled

The framework is intentionally subsystem‑level, not RTL‑level. It uses telemetry to reason about:

- **DRAM / Memory** – ECC correctable error bursts, memory bandwidth saturation, and tail latency spikes, classified as memory/ECC stress incidents.  
- **PCIe** – PCIe AER‑like events used as signals in RCA rules to infer link instability, retries, or resets.  
- **Networking** – packet drops and congestion signatures under bursty traffic, interpreted as queue saturation or congestion.  
- **CPU / Power / Thermal** – frequency drops combined with rising temperature, identified as thermal throttling or power‑management‑driven slowdowns.

The key is not just logging these signals, but correlating, ranking, and explaining their interaction during each incident window.

***

## Post-silicon validation mindset

This project is deliberately framed as post‑silicon rather than pre‑silicon simulation.

For every incident, the tool encourages a validation‑style loop:

1. Failure signature – what pattern appeared in telemetry?  
2. Reproduce – which workload and conditions should be re‑run in the lab?  
3. Isolate – which subsystem(s) and counters are most implicated?  
4. Mitigate – what operational or firmware changes might help?  
5. Regression – which new regression test should be added so this signature cannot escape again?

This mirrors how lab validation, fleet issue triage, and silicon enablement teams operate when closing the loop between the field and coverage.

***

## CLI workflow

**silicon-rca** is designed to behave like an internal debug tool rather than a notebook. The CLI:

- Ingests telemetry from CSV/JSON‑style inputs (counters plus events).  
- Runs anomaly detection and incident windowing.  
- Applies an explainable rule‑based RCA engine.  
- Emits:
  - Per‑incident CSVs.  
  - Plots for key signals over time.  
  - A Markdown executive report with summaries, incidents, and suggested next steps.

Example (adjust to your actual entrypoint once you wire up the CLI):

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run RCA on an example dataset
python -m silicon-rca.cli \
  --counters data/counters.csv \
  --events data/events.csv \
  --output_dir out/
```

After running, open `out/report.md` to see a human‑readable incident and RCA summary suitable for sharing with a silicon debug or validation team.

***

## Project structure

Adapt this outline to match your actual directory layout in `main`:

```text
silicon-rca/
  silicon-rca/
    __init__.py
    cli.py          # CLI entrypoint for the full pipeline
    ingest.py       # Input loading & normalization
    correlate.py    # Time alignment & correlation across hosts
    detect.py       # MAD-based anomaly / incident detection
    rca.py          # Explainable rule-based RCA engine
    report.py       # Markdown / CSV / plot generation
  data/
    counters.csv    # Example counters for multiple hosts/workloads
    events.csv      # Example silicon events (ECC, PCIe, etc.)
  requirements.txt
  README.md
```

***

## What this project demonstrates

You can confidently use this project to demonstrate:

- **Silicon lifecycle thinking** – data‑center, workload‑aware understanding of how silicon behaves in production from deployment through failure and feedback.  
- **Troubleshooting, debug & analytics** – ability to build structured pipelines that ingest telemetry, detect incidents, and explain what matters and why.  
- **Subsystem‑level hardware reasoning** – reasoning about CPU, memory/DRAM, PCIe, networking, and thermal/power domains from counters and events.  
- **Post‑silicon validation workflows** – bring‑up/debug‑style thinking plus explicit "failure signature → reproduce → isolate → mitigate → regression" loops.


***
