"""Single-core population-size benchmark for the BAC NEM and CCM models.

The timed region is one complete optimization:

1. scipy.optimize.differential_evolution
2. scipy.optimize.minimize(method="Nelder-Mead")

The problem definitions are copied from ``bac_test.py`` and
``bac_ccm_test.py``.  Results are written beside this script by default.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

# Keep both SciPy and the native numerical runtimes on one worker/thread.  These
# values must be set before importing NumPy/SciPy.
for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_variable] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIBRARY = PROJECT_ROOT / "packaging" / "lib" / "libiphreeqc-3.8.6.dylib"
if DEFAULT_LIBRARY.is_file():
    os.environ.setdefault("PHREEFIT_IPHREEQC_LIBRARY", str(DEFAULT_LIBRARY))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize
from threadpoolctl import threadpool_limits
from tqdm import tqdm

from src_new import main_cal


TEST_DIR = Path(__file__).resolve().parent
DATA_FILE = TEST_DIR / "bacteria.csv"
DATABASE_FILE = TEST_DIR / "simple_davies_for_titration.dat"
DEFAULT_POPSIZES = (5, 8, 10, 15, 20)
MODEL_SETTINGS = {
    "NEM": {"strategy": "best1bin", "recombination": 0.8},
    "CCM": {"strategy": "best1exp", "recombination": 0.9},
}


def build_problem(model: str):
    """Build a fresh BAC optimization problem matching the existing tests."""
    data = np.loadtxt(DATA_FILE, delimiter=",", skiprows=1)
    database = DATABASE_FILE.read_text(encoding="UTF-8")

    surface_a = main_cal.SurfaceSpecies2()
    surface_b = main_cal.SurfaceSpecies2()
    surface_c = main_cal.SurfaceSpecies2()
    surface_a.add_surface(
        "Surf_a", "Surf_aH", (0, 0.01), 140, 0.9705, 1, 1, 0.001, 1, 1
    )
    surface_a.add_reactions(
        "Surf_aH = Surf_a- + H+", (-11, -2), 1, True, 1, -5, -1
    )
    surface_b.add_surface(
        "Surf_b", "Surf_bH", (0, 0.01), 140, 0.9705, 1, 1, 0.001, 1, 1
    )
    surface_b.add_reactions(
        "Surf_bH = Surf_b- + H+", (-11, -2), 1, True, 1, -5, -1
    )

    if model == "NEM":
        surface_c.add_surface(
            "Surf_c", "Surf_cH", (0, 0.01), 140, 0.9705, 1, 1, 0.001, 1, 1
        )
        surface_c.add_reactions(
            "Surf_cH = Surf_c- + H+", (-11, -2), 1, True, 1, -5, -1
        )
        surface_d = main_cal.SurfaceSpecies2()
        surface_d.add_surface(
            "Surf_d", "Surf_dH", (0, 0.01), 140, 0.9705, 1, 1, 0.001, 1, 1
        )
        surface_d.add_reactions(
            "Surf_dH = Surf_d- + H+", (-11, -2), 1, True, 1, -5, -1
        )
    elif model == "CCM":
        surface_c.add_surface(
            "Surf_c", "Surf_cH", (0, 0.01), 140, 0.9705, (0, 5), 1, 0.001, 1, 1
        )
        surface_c.add_reactions(
            "Surf_cH = Surf_c- + H+", (-11, -2), 1, True, 1, -5, -1
        )
    else:
        raise ValueError(f"Unsupported model: {model}")

    titration = main_cal.Adsorption(model)
    titration.species_definition(database, "")
    titration.initial_solution(
        [0.1], initial_pH=2.449, cation="Na", anion="Cl", metal={}
    )
    titration.add_surface(surface_a)
    titration.add_surface(surface_b)
    titration.add_surface(surface_c)
    if model == "NEM":
        titration.add_surface(surface_d)
    titration.selected_output({})
    titration.set_type_acid(type_base="NaOH", type_acid="HNO3")
    titration.mix_solution(type_solution="dissolution", base_mass=0.993)
    titration.mix_action(initial_volume=6.509, mix_volume=data[:, 1])
    titration.get_bounds()
    return data, titration


def run_experiment(
    model: str,
    popsize: int,
    run_id: int,
    seed: int,
    de_maxiter: int,
) -> dict:
    """Run one independent, complete optimization and return one result row."""
    data, titration = build_problem(model)
    settings = MODEL_SETTINGS[model]
    parameter_count = len(titration.bounds)
    started = time.perf_counter()

    try:
        de_result = differential_evolution(
            main_cal.proto_fun,
            titration.bounds,
            args=(data[:, 0], titration, True),
            strategy=settings["strategy"],
            maxiter=de_maxiter,
            popsize=popsize,
            recombination=settings["recombination"],
            init="halton",
            polish=False,
            rng=seed,
            workers=1,
            updating="immediate",
        )
        nm_result = minimize(
            main_cal.proto_fun,
            de_result.x,
            args=(data[:, 0], titration, True),
            method="Nelder-Mead",
            bounds=np.asarray(titration.bounds),
            options={"adaptive": True},
        )
        chosen_result = nm_result if nm_result.success else de_result
        elapsed = time.perf_counter() - started
        return {
            "model": model,
            "popsize": popsize,
            "run_id": run_id,
            "seed": seed,
            "parameter_count": parameter_count,
            "nominal_population_members": popsize * parameter_count,
            "strategy": settings["strategy"],
            "recombination": settings["recombination"],
            "init": "halton",
            "de_maxiter": de_maxiter,
            "elapsed_seconds": elapsed,
            "de_fun": float(de_result.fun),
            "de_nfev": int(de_result.nfev),
            "de_nit": int(de_result.nit),
            "de_success": bool(de_result.success),
            "nm_fun": float(nm_result.fun),
            "nm_nfev": int(nm_result.nfev),
            "nm_nit": int(nm_result.nit),
            "nm_success": bool(nm_result.success),
            "final_fun": float(chosen_result.fun),
            "completed": True,
            "error": "",
        }
    except Exception as error:
        return {
            "model": model,
            "popsize": popsize,
            "run_id": run_id,
            "seed": seed,
            "parameter_count": parameter_count,
            "nominal_population_members": popsize * parameter_count,
            "strategy": settings["strategy"],
            "recombination": settings["recombination"],
            "init": "halton",
            "de_maxiter": de_maxiter,
            "elapsed_seconds": time.perf_counter() - started,
            "de_fun": np.nan,
            "de_nfev": np.nan,
            "de_nit": np.nan,
            "de_success": False,
            "nm_fun": np.nan,
            "nm_nfev": np.nan,
            "nm_nit": np.nan,
            "nm_success": False,
            "final_fun": np.nan,
            "completed": False,
            "error": "".join(traceback.format_exception_only(type(error), error)).strip(),
        }
    finally:
        main_cal.close_cached_iphreeqc()


def summarize(raw_results: pd.DataFrame) -> pd.DataFrame:
    """Produce model/popsize timing and objective statistics."""
    rows = []
    for (model, popsize), group in raw_results.groupby(["model", "popsize"], sort=True):
        completed = group[group["completed"]]
        rows.append(
            {
                "model": model,
                "popsize": int(popsize),
                "runs": int(len(group)),
                "completed_runs": int(len(completed)),
                "failed_runs": int(len(group) - len(completed)),
                "completion_rate": len(completed) / len(group),
                "parameter_count": int(group["parameter_count"].iloc[0]),
                "nominal_population_members": int(
                    group["nominal_population_members"].iloc[0]
                ),
                "mean_attempt_seconds": group["elapsed_seconds"].mean(),
                "std_attempt_seconds": group["elapsed_seconds"].std(ddof=1),
                "mean_completed_seconds": completed["elapsed_seconds"].mean(),
                "std_completed_seconds": completed["elapsed_seconds"].std(ddof=1),
                "median_completed_seconds": completed["elapsed_seconds"].median(),
                "min_completed_seconds": completed["elapsed_seconds"].min(),
                "max_completed_seconds": completed["elapsed_seconds"].max(),
                "mean_final_fun": completed["final_fun"].mean(),
                "std_final_fun": completed["final_fun"].std(ddof=1),
                "median_final_fun": completed["final_fun"].median(),
                "best_final_fun": completed["final_fun"].min(),
                "mean_de_nfev": completed["de_nfev"].mean(),
                "mean_nm_nfev": completed["nm_nfev"].mean(),
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models", nargs="+", choices=tuple(MODEL_SETTINGS), default=["NEM", "CCM"]
    )
    parser.add_argument("--popsizes", nargs="+", type=int, default=DEFAULT_POPSIZES)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--de-maxiter", type=int, default=1000)
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=TEST_DIR / "bac_popsize",
        help="Path prefix used for the raw and summary CSV files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.repeats < 1 or args.de_maxiter < 1 or any(p < 1 for p in args.popsizes):
        raise ValueError("repeats, de-maxiter, and every popsize must be positive")

    experiments = [
        (model, popsize, run_id, (run_id + 1) * 42, args.de_maxiter)
        for model in args.models
        for popsize in args.popsizes
        for run_id in range(args.repeats)
    ]
    print(
        f"Running {len(experiments)} complete BAC optimizations serially "
        "with workers=1 and native thread pools limited to 1."
    )
    print(
        "IPhreeqc library: "
        f"{os.environ.get('PHREEFIT_IPHREEQC_LIBRARY', 'phreeqpy default')}"
    )

    with threadpool_limits(limits=1):
        rows = [
            run_experiment(*experiment)
            for experiment in tqdm(experiments, desc="BAC popsize", unit="run")
        ]

    raw_results = pd.DataFrame(rows)
    summary = summarize(raw_results)
    output_prefix = args.output_prefix.resolve()
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_file = output_prefix.with_name(output_prefix.name + "_raw_results.csv")
    summary_file = output_prefix.with_name(output_prefix.name + "_summary.csv")
    raw_results.to_csv(raw_file, index=False)
    summary.to_csv(summary_file, index=False)

    print("\nSummary:")
    print(summary.to_string(index=False))
    print(f"\nRaw results: {raw_file}")
    print(f"Summary:     {summary_file}")


if __name__ == "__main__":
    main()
