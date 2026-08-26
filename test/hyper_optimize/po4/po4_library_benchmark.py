"""Run paired full PO4 optimizations against one selected IPhreeqc library."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import statistics
import sys
import time

import pandas as pd
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--popsize", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    dll = args.dll.resolve()
    output = args.output.resolve()
    os.environ["PHREEFIT_IPHREEQC_LIBRARY"] = str(dll)
    sys.path.insert(0, str(TEST_DIR))

    # Import only after selecting the library. Spawned workers inherit the same
    # environment variable and execute the real PO4/main_cal objective path.
    import po4_popsize_test as po4  # noqa: PLC0415

    experiments = [
        {"popsize": args.popsize, "run_id": run_id}
        for run_id in range(args.runs)
    ]
    results = []
    wall_started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(po4.run_single_experiment, experiment)
            for experiment in experiments
        ]
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc=f"PO4 full optimization ({dll.name})",
        ):
            results.append(future.result())
    wall_seconds = time.perf_counter() - wall_started

    raw = pd.DataFrame(results).sort_values("run_id")
    successful = raw[raw["error"].isna()]
    times = successful["time"].tolist()
    payload = {
        "dll": str(dll),
        "runs": args.runs,
        "workers": args.workers,
        "popsize": args.popsize,
        "seeds": raw["seed"].astype(int).tolist(),
        "successes": int(len(successful)),
        "failures": int(args.runs - len(successful)),
        "wall_seconds": wall_seconds,
        "run_time_mean_seconds": statistics.mean(times) if times else None,
        "run_time_median_seconds": statistics.median(times) if times else None,
        "run_time_min_seconds": min(times) if times else None,
        "run_time_max_seconds": max(times) if times else None,
        "total_nfev_mean": (
            float(successful["total_nfev"].mean()) if len(successful) else None
        ),
        "fun_mean": float(successful["fun"].mean()) if len(successful) else None,
        "fun_min": float(successful["fun"].min()) if len(successful) else None,
        "results": raw.to_dict(orient="records"),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in payload.items() if key != "results"}, indent=2))
    print(f"Results written to {output}")


if __name__ == "__main__":
    main()
