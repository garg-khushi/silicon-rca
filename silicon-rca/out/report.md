# Post-Silicon Failure RCA Report

## Executive Summary

- Total incidents detected: **8**

- Top root-cause categories:

  - **DRAM/ECC or memory-controller stress**: 3

  - **Thermal throttling / power management**: 3

  - **Network congestion / queue saturation**: 2


## Top Incidents (by severity)

| incident_id   | host    | workload        | event_hint         |   severity_score | top_signals                                      |
|:--------------|:--------|:----------------|:-------------------|-----------------:|:-------------------------------------------------|
| INC_0001      | host_02 | network_burst   | NETWORK_CONGESTION |         50       | net_drops:+50.6,mem_bw:+2.7,freq_ghz:-2.6        |
| INC_0003      | host_07 | network_burst   | NETWORK_CONGESTION |         40.9926  | net_drops:+33.7,ecc_ce:+4.0,cpu_util:+3.2        |
| INC_0000      | host_00 | ai_train        | DRAM_ECC           |         30.2001  | ecc_ce:+21.6,mem_latency_p99:+4.5,mem_bw:-4.1    |
| INC_0007      | host_11 | ai_train        | DRAM_ECC           |         29.7458  | ecc_ce:+21.6,mem_latency_p99:+4.1,net_drops:+4.0 |
| INC_0002      | host_04 | video_transcode | DRAM_ECC           |         27.9704  | ecc_ce:+20.2,mem_latency_p99:+4.9,mem_bw:-2.8    |
| INC_0006      | host_09 | ai_train        | THERMAL            |         11.0544  | freq_ghz:-4.4,temp_c:+4.3,mem_latency_p99:+2.3   |
| INC_0004      | host_09 | ai_train        | THERMAL            |          9.95743 | temp_c:+4.6,freq_ghz:-4.0,mem_latency_p99:-1.3   |
| INC_0005      | host_09 | ai_train        | THERMAL            |          9.39396 | freq_ghz:-4.5,temp_c:+3.3,mem_latency_p99:-1.6   |

## RCA Results (Top 10)

| incident_id   | root_cause                            |   confidence | explanation                                                                 |
|:--------------|:--------------------------------------|-------------:|:----------------------------------------------------------------------------|
| INC_0001      | Network congestion / queue saturation |         0.62 | Drops + bursty networking workload indicates congestion or queue saturation |
| INC_0003      | Network congestion / queue saturation |         0.62 | Drops + bursty networking workload indicates congestion or queue saturation |
| INC_0000      | DRAM/ECC or memory-controller stress  |         0.64 | ECC bursts + tail latency + high bandwidth suggest memory subsystem stress  |
| INC_0007      | DRAM/ECC or memory-controller stress  |         0.64 | ECC bursts + tail latency + high bandwidth suggest memory subsystem stress  |
| INC_0002      | DRAM/ECC or memory-controller stress  |         0.64 | ECC bursts + tail latency + high bandwidth suggest memory subsystem stress  |
| INC_0006      | Thermal throttling / power management |         0.5  | Thermal excursion and frequency drop patterns suggest throttling            |
| INC_0004      | Thermal throttling / power management |         0.5  | Thermal excursion and frequency drop patterns suggest throttling            |
| INC_0005      | Thermal throttling / power management |         0.38 | Thermal excursion and frequency drop patterns suggest throttling            |

## Recommended Next Actions

### INC_0001 — Network congestion / queue saturation (conf 0.62)

- **Why:** Drops + bursty networking workload indicates congestion or queue saturation

- **Validation:** Generate bursty traffic; collect drops, queue depth (if modeled), retransmits; verify congestion control behavior under peak load.

- **Mitigation:** Tune queue thresholds and traffic shaping; add regression test for drop spikes under network burst signature.

### INC_0003 — Network congestion / queue saturation (conf 0.62)

- **Why:** Drops + bursty networking workload indicates congestion or queue saturation

- **Validation:** Generate bursty traffic; collect drops, queue depth (if modeled), retransmits; verify congestion control behavior under peak load.

- **Mitigation:** Tune queue thresholds and traffic shaping; add regression test for drop spikes under network burst signature.

### INC_0000 — DRAM/ECC or memory-controller stress (conf 0.64)

- **Why:** ECC bursts + tail latency + high bandwidth suggest memory subsystem stress

- **Validation:** Reproduce under ai_train/video_transcode with sustained memory bandwidth; collect ECC counters, mem latency histograms, bandwidth, and error addresses if available.

- **Mitigation:** Check ECC thresholding, memory timing margins, and firmware; add regression test for ECC burst + latency spike signature.

### INC_0007 — DRAM/ECC or memory-controller stress (conf 0.64)

- **Why:** ECC bursts + tail latency + high bandwidth suggest memory subsystem stress

- **Validation:** Reproduce under ai_train/video_transcode with sustained memory bandwidth; collect ECC counters, mem latency histograms, bandwidth, and error addresses if available.

- **Mitigation:** Check ECC thresholding, memory timing margins, and firmware; add regression test for ECC burst + latency spike signature.

### INC_0002 — DRAM/ECC or memory-controller stress (conf 0.64)

- **Why:** ECC bursts + tail latency + high bandwidth suggest memory subsystem stress

- **Validation:** Reproduce under ai_train/video_transcode with sustained memory bandwidth; collect ECC counters, mem latency histograms, bandwidth, and error addresses if available.

- **Mitigation:** Check ECC thresholding, memory timing margins, and firmware; add regression test for ECC burst + latency spike signature.

### INC_0006 — Thermal throttling / power management (conf 0.50)

- **Why:** Thermal excursion and frequency drop patterns suggest throttling

- **Validation:** Run sustained compute load; record temp, freq, perf counters; verify throttling triggers and thermal headroom across racks.

- **Mitigation:** Improve thermal policy/limits, ensure cooling and fan curves; add regression for perf drop under thermal excursion signature.

### INC_0004 — Thermal throttling / power management (conf 0.50)

- **Why:** Thermal excursion and frequency drop patterns suggest throttling

- **Validation:** Run sustained compute load; record temp, freq, perf counters; verify throttling triggers and thermal headroom across racks.

- **Mitigation:** Improve thermal policy/limits, ensure cooling and fan curves; add regression for perf drop under thermal excursion signature.

### INC_0005 — Thermal throttling / power management (conf 0.38)

- **Why:** Thermal excursion and frequency drop patterns suggest throttling

- **Validation:** Run sustained compute load; record temp, freq, perf counters; verify throttling triggers and thermal headroom across racks.

- **Mitigation:** Improve thermal policy/limits, ensure cooling and fan curves; add regression for perf drop under thermal excursion signature.
