import random
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


FLEET_SIZE = 12
DURATION_SEC = 1800  # 30 minutes
SEED = 42

WORKLOADS = ["ai_train", "video_transcode", "network_burst", "idle"]
FAILURE_TYPES = ["dram_ecc", "pcie_aer", "thermal", "network_congestion"]


def generate_fleet_ids(n):
    return [f"host_{i:02d}" for i in range(n)]


def generate_time_index(start, duration):
    return [start + timedelta(seconds=i) for i in range(duration)]


def base_counters(workload):
    if workload == "ai_train":
        return dict(cpu=75, mem_bw=80, latency=90, net=20)
    if workload == "video_transcode":
        return dict(cpu=65, mem_bw=60, latency=70, net=40)
    if workload == "network_burst":
        return dict(cpu=40, mem_bw=30, latency=50, net=85)
    return dict(cpu=20, mem_bw=20, latency=30, net=10)


def inject_failure(row, failure):
    if failure == "dram_ecc":
        row["ecc_ce"] += random.randint(10, 30)
        row["mem_latency_p99"] += random.randint(20, 50)
    elif failure == "pcie_aer":
        row["pcie_aer"] += random.randint(5, 15)
    elif failure == "thermal":
        row["temp_c"] += random.randint(10, 20)
        row["freq_ghz"] -= random.uniform(0.5, 1.0)
    elif failure == "network_congestion":
        row["net_drops"] += random.randint(50, 150)
    return row


def simulate():
    random.seed(SEED)
    np.random.seed(SEED)

    out_dir = Path("data/demo_fleet")
    out_dir.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now()
    times = generate_time_index(start_time, DURATION_SEC)
    hosts = generate_fleet_ids(FLEET_SIZE)

    counter_rows = []
    log_events = []

    for host in hosts:
        workload = random.choice(WORKLOADS)
        base = base_counters(workload)

        failure = random.choice(FAILURE_TYPES + [None])
        failure_start = random.randint(300, 1200) if failure else None
        failure_end = failure_start + random.randint(60, 180) if failure else None

        for i, ts in enumerate(times):
            row = {
                "timestamp": ts,
                "host": host,
                "workload": workload,
                "cpu_util": np.clip(np.random.normal(base["cpu"], 5), 0, 100),
                "mem_bw": np.clip(np.random.normal(base["mem_bw"], 8), 0, 100),
                "mem_latency_p99": np.clip(np.random.normal(base["latency"], 10), 0, 200),
                "ecc_ce": max(0, int(np.random.poisson(1))),
                "pcie_aer": max(0, int(np.random.poisson(0.2))),
                "net_drops": max(0, int(np.random.poisson(5))),
                "temp_c": np.clip(np.random.normal(65, 5), 40, 100),
                "freq_ghz": np.clip(np.random.normal(2.8, 0.2), 1.0, 3.5),
            }

            if failure and failure_start <= i <= failure_end:
                row = inject_failure(row, failure)
                log_events.append({
                    "timestamp": ts.isoformat(),
                    "host": host,
                    "event": failure.upper(),
                    "severity": "WARN"
                })

            counter_rows.append(row)

    pd.DataFrame(counter_rows).to_csv(out_dir / "counters.csv", index=False)

    with open(out_dir / "logs.jsonl", "w") as f:
        for e in log_events:
            f.write(json.dumps(e) + "\n")

    print("Fleet telemetry generated in data/demo_fleet/")


if __name__ == "__main__":
    simulate()
