"""Micro-benchmark IPhreeqc lifecycle and PhreeFit CCM/CD-MUSIC workloads."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
import time
from pathlib import Path

from phreeqpy.iphreeqc.phreeqc_dll import IPhreeqc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src_new.main_cal import Adsorption, SurfaceSpecies2


DATABASE_PATH = ROOT / "test" / "bac" / "simple_davies_for_titration.dat"
DATA_PATH = ROOT / "test" / "bac" / "bacteria.csv"
DELETE_ALL = "DELETE\n    -all\nEND\n"
DISABLE_SELECTED_OUTPUT = "PRINT\n    -selected_output false\nEND\n"


def now() -> float:
    return time.perf_counter()


def summarize(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "mean_ms": 1000 * statistics.mean(values),
        "median_ms": 1000 * statistics.median(values),
        "p95_ms": 1000 * ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)],
        "min_ms": 1000 * ordered[0],
        "max_ms": 1000 * ordered[-1],
    }


def read_volumes(limit: int) -> list[float]:
    with DATA_PATH.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        return [float(row["vol"]) for row in rows][:limit]


def make_problem(model: str, points: int) -> Adsorption:
    database = DATABASE_PATH.read_text(encoding="utf-8")
    problem = Adsorption(model)
    problem.species_definition(database, "")
    problem.initial_solution([0.1], initial_pH=2.449, cation="Na", anion="Cl", metal={})

    for suffix in ("a", "b", "c"):
        species = SurfaceSpecies2()
        species.add_surface(
            f"Surf_{suffix}",
            f"Surf_{suffix}H",
            (1e-5, 0.01),
            140,
            0.9705,
            (0.1, 5.0),
            (0.1, 5.0),
            0.001,
            1.0,
            1.0,
        )
        species.add_reactions(
            f"Surf_{suffix}H = Surf_{suffix}- + H+",
            (-11.0, -2.0),
            0.0,
            True,
            -1.0,
            -5.0,
            0.0,
        )
        problem.add_surface(species)

    problem.selected_output({})
    problem.output += """
        USER_PUNCH 1
            -headings iterations
            -start
            10 PUNCH ITERATIONS
            -end
    """
    problem.set_type_acid(type_base="NaOH", type_acid="HNO3")
    problem.mix_solution(type_solution="dissolution", base_mass=0.993)
    problem.mix_action(initial_volume=6.509, mix_volume=read_volumes(points))
    problem.get_bounds()
    return problem


def candidate_vectors(problem: Adsorption, repeats: int) -> list[list[float]]:
    base = list(problem.initial_guess)
    vectors = []
    for index in range(repeats):
        scale = 1.0 + 0.03 * math.sin(index * 0.7)
        candidate = []
        for value, bounds in zip(base, problem.bounds):
            low, high = bounds
            shifted = value * scale if value else 0.01 * math.sin(index + 1)
            candidate.append(min(high, max(low, shifted)))
        vectors.append(candidate)
    return vectors


def script_for(problem: Adsorption, candidate: list[float]) -> str:
    problem.set_para(candidate)
    problem.create_script(mix=True)
    return problem.total


def extract_columns(instance: IPhreeqc) -> tuple[list[object], list[float], list[float]]:
    headings = instance.get_selected_output_row(0)
    ph_index = headings.index("pH")
    iterations_index = headings.index("iterations")
    ph = instance.get_selected_output_column(ph_index)[1:]
    iterations = instance.get_selected_output_column(iterations_index)[1:]
    return headings, ph, iterations


def fresh_runs(dll: str, database: str, scripts: list[str]) -> tuple[dict, list[list[float]]]:
    samples = {key: [] for key in ("create", "load_database", "run", "extract", "destroy", "total")}
    outputs = []
    for script in scripts:
        total_start = now()
        start = now()
        instance = IPhreeqc(dll)
        samples["create"].append(now() - start)
        start = now()
        instance.load_database_string(database)
        samples["load_database"].append(now() - start)
        start = now()
        instance.run_string(script)
        samples["run"].append(now() - start)
        start = now()
        _, ph, _ = extract_columns(instance)
        samples["extract"].append(now() - start)
        outputs.append(ph)
        start = now()
        instance.destroy_iphreeqc()
        samples["destroy"].append(now() - start)
        samples["total"].append(now() - total_start)
    return {key: summarize(value) for key, value in samples.items()}, outputs


def persistent_runs(
    dll: str,
    database: str,
    scripts: list[str],
    delete_all: bool,
) -> tuple[dict, list[list[float]], list[list[float]]]:
    instance = IPhreeqc(dll)
    instance.load_database_string(database)
    run_times = []
    extract_times = []
    outputs = []
    iterations = []
    try:
        for script in scripts:
            start = now()
            prefix = DISABLE_SELECTED_OUTPUT + (DELETE_ALL if delete_all else "")
            instance.run_string(prefix + script)
            run_times.append(now() - start)
            start = now()
            _, ph, iteration_values = extract_columns(instance)
            extract_times.append(now() - start)
            outputs.append(ph)
            iterations.append(iteration_values)
    finally:
        instance.destroy_iphreeqc()
    return {
        "run": summarize(run_times),
        "extract": summarize(extract_times),
        "run_plus_extract": summarize([a + b for a, b in zip(run_times, extract_times)]),
    }, outputs, iterations


def max_output_difference(left: list[list[float]], right: list[list[float]]) -> float:
    differences = []
    for left_run, right_run in zip(left, right):
        differences.extend(abs(float(a) - float(b)) for a, b in zip(left_run, right_run))
    return max(differences, default=0.0)


def output_extraction_benchmark(dll: str, database: str, script: str, repeats: int = 100) -> dict:
    instance = IPhreeqc(dll)
    instance.load_database_string(database)
    instance.run_string(script)
    headings = instance.get_selected_output_row(0)
    row_count = instance.row_count
    ph_index = headings.index("pH")
    full_times = []
    column_times = []
    try:
        for _ in range(repeats):
            start = now()
            instance.get_selected_output_array()
            full_times.append(now() - start)
            start = now()
            instance.get_selected_output_column(ph_index)
            column_times.append(now() - start)
    finally:
        instance.destroy_iphreeqc()
    return {
        "shape": [row_count, len(headings)],
        "full_array": summarize(full_times),
        "ph_column": summarize(column_times),
        "speedup": statistics.mean(full_times) / statistics.mean(column_times),
    }


def run_model(dll: str, model: str, repeats: int, points: int) -> dict:
    problem = make_problem(model, points)
    scripts = [script_for(problem, vector) for vector in candidate_vectors(problem, repeats)]
    database = problem.database

    # Warm dynamic loading and code pages before timing.
    warmup = IPhreeqc(dll)
    warmup.load_database_string(database)
    warmup.run_string(scripts[0])
    warmup.destroy_iphreeqc()

    fresh, fresh_outputs = fresh_runs(dll, database, scripts)
    persistent, persistent_outputs, iterations = persistent_runs(dll, database, scripts, False)
    persistent_delete, delete_outputs, delete_iterations = persistent_runs(dll, database, scripts, True)
    return {
        "model": model,
        "points": points,
        "parameters": len(problem.initial_guess),
        "script_bytes": len(scripts[0].encode("utf-8")),
        "database_bytes": len(database.encode("utf-8")),
        "fresh": fresh,
        "persistent": persistent,
        "persistent_delete_all": persistent_delete,
        "persistent_max_abs_ph_difference": max_output_difference(fresh_outputs, persistent_outputs),
        "delete_max_abs_ph_difference": max_output_difference(fresh_outputs, delete_outputs),
        "persistent_iterations_mean": statistics.mean(float(v) for row in iterations for v in row),
        "delete_iterations_mean": statistics.mean(float(v) for row in delete_iterations for v in row),
        "output_extraction": output_extraction_benchmark(dll, database, scripts[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--points", type=int, default=20)
    parser.add_argument("--models", nargs="+", choices=("CCM", "CDMUSIC"), default=("CCM", "CDMUSIC"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = {
        "label": args.label,
        "dll": str(Path(args.dll).resolve()),
        "database_sha256": hashlib.sha256(DATABASE_PATH.read_bytes()).hexdigest(),
        "repeats": args.repeats,
        "models": [run_model(args.dll, model, args.repeats, args.points) for model in args.models],
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
