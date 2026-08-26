"""Capture and replay a BAC CCM parameter vector that triggers an error."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import bac_popsize_test as benchmark
import numpy as np
from scipy.optimize import differential_evolution, minimize


def evaluate(parameters: list[float]) -> dict:
    data, problem = benchmark.build_problem("CCM")
    try:
        value = benchmark.main_cal.proto_fun(
            np.asarray(parameters), data[:, 0], problem, True
        )
        return {"completed": True, "objective": float(value), "error": ""}
    except Exception as error:
        return {"completed": False, "objective": None, "error": str(error)}
    finally:
        benchmark.main_cal.close_cached_iphreeqc()


def capture(seed: int) -> dict:
    data, problem = benchmark.build_problem("CCM")
    state = {"stage": "differential_evolution", "evaluation": 0}

    def traced_objective(parameters, exp_data, titration, mix):
        state["evaluation"] += 1
        try:
            return benchmark.main_cal.proto_fun(parameters, exp_data, titration, mix)
        except Exception as error:
            state["parameters"] = np.asarray(parameters).tolist()
            state["error"] = str(error)
            raise

    try:
        de_result = differential_evolution(
            traced_objective,
            problem.bounds,
            args=(data[:, 0], problem, True),
            strategy="best1exp",
            maxiter=1000,
            popsize=8,
            recombination=0.9,
            init="halton",
            polish=False,
            rng=seed,
            workers=1,
            updating="immediate",
        )
        state["stage"] = "Nelder-Mead"
        minimize(
            traced_objective,
            de_result.x,
            args=(data[:, 0], problem, True),
            method="Nelder-Mead",
            bounds=np.asarray(problem.bounds),
            options={"adaptive": True},
        )
        state["error"] = "No error was produced"
    except Exception:
        pass
    finally:
        benchmark.main_cal.close_cached_iphreeqc()
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-seed", type=int)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.capture_seed is None) == (args.replay is None):
        parser.error("select exactly one of --capture-seed and --replay")

    if args.capture_seed is not None:
        result = capture(args.capture_seed)
        result.update({"mode": "capture", "seed": args.capture_seed, "popsize": 8})
    else:
        captured = json.loads(args.replay.read_text(encoding="utf-8"))
        result = evaluate(captured["parameters"])
        result.update(
            {
                "mode": "replay",
                "source": str(args.replay.resolve()),
                "source_seed": captured["seed"],
                "parameters": captured["parameters"],
            }
        )
    result["library"] = os.environ.get(
        "PHREEFIT_IPHREEQC_LIBRARY", "phreeqpy default"
    )
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
