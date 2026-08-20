"""Benchmark PO4 CD-MUSIC objective calls without running the DE optimizer."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll", required=True)
    parser.add_argument("--candidates", type=int, default=50)
    parser.add_argument("--seed", type=int, default=386)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    os.environ["PHREEFIT_IPHREEQC_LIBRARY"] = str(Path(args.dll).resolve())
    sys.path.insert(0, str(ROOT / "test" / "po4"))
    from po4_popsize_test import build_problem
    from src_new import main_cal

    data, titration = build_problem()
    rng = np.random.default_rng(args.seed)
    bounds = np.asarray(titration.bounds, dtype=float)
    candidates = rng.uniform(bounds[:, 0], bounds[:, 1],
                             size=(args.candidates, len(bounds)))
    objective_args = (
        data.iloc[:, 1].values,
        data.groupby("IS", sort=False),
        "",
        titration,
    )

    # Warm the dynamic loader and the per-process cached IPhreeqc instance.
    main_cal.advanced_fun_auto(candidates[0], *objective_args)
    elapsed = []
    values = []
    try:
        for candidate in candidates:
            started = time.perf_counter()
            values.append(float(main_cal.advanced_fun_auto(candidate, *objective_args)))
            elapsed.append(time.perf_counter() - started)
    finally:
        main_cal.close_cached_iphreeqc()

    ordered = sorted(elapsed)
    result = {
        "dll": str(Path(args.dll).resolve()),
        "candidates": args.candidates,
        "points": len(data),
        "parameters": len(bounds),
        "mean_ms": statistics.mean(elapsed) * 1000,
        "median_ms": statistics.median(elapsed) * 1000,
        "p95_ms": ordered[max(0, int(np.ceil(0.95 * len(ordered))) - 1)] * 1000,
        "failures": 0,
        "objective_values": values,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
