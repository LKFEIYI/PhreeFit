"""Compare differential-evolution population sizes with the PO4 example.

This keeps the DE settings selected by the earlier PO4 grid search fixed and
changes only ``popsize``. Five population sizes with ten deterministic repeats
produce 50 experiments in total.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from scipy import optimize
from scipy.optimize import differential_evolution as de_opt
from sklearn.model_selection import ParameterGrid
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = Path(__file__).resolve().parent
IPHREEQC_LIBRARY = (
    PROJECT_ROOT / "packaging" / "lib" / "libiphreeqc-3.8.6.dylib"
)

# Use the optimized 3.8.6 library unless the caller explicitly selects another
# build. This assignment is inherited by spawned worker processes.
os.environ.setdefault("PHREEFIT_IPHREEQC_LIBRARY", str(IPHREEQC_LIBRARY))
sys.path.insert(0, str(PROJECT_ROOT))

from src_new import main_cal  # noqa: E402


POPSIZES = [5, 8, 10, 15, 20]
REPEATS_PER_POPSIZE = 10
RANDOM_SEED_MULTIPLIER = 42
NUM_WORKERS = 4


def build_problem():
    database = (TEST_DIR / "simple_PO_davies.dat").read_text(encoding="UTF-8")
    data = pd.read_csv(TEST_DIR / "po2.csv")
    data.columns = ["pH", "volume", "IS"]

    surface_a = main_cal.SurfaceSpecies2()
    surface_b = main_cal.SurfaceSpecies2()

    surface_a.add_surface(
        "Surf_a", "Surf_aOH-0.5", 3.49e-3, 350, 1, 0.74, 0.93, 0.001, 1, 1
    )
    surface_a.add_reactions(
        "Surf_aOH-0.5  + H+ = Surf_aOH2+0.5", 8.7, 0, True, 1, -5, -1
    )
    surface_a.add_reactions(
        "Surf_aOH-0.5 + K+  = Surf_aOHK+0.5", -1.16, 1, True, 1, -5, -1
    )
    surface_a.add_reactions(
        "Surf_aOH-0.5 + H+ + NO3- = Surf_aOH2NO3-0.5",
        7.74,
        -1,
        True,
        0,
        -5,
        -1,
    )
    surface_a.add_reactions(
        "2Surf_aOH-0.5 + 2H+ + PO4-3 = Surf_a2PO4-2 + 2H2O",
        (20, 40),
        (-3, 0),
        True,
        -1,
        -5,
        -1,
    )
    surface_a.add_reactions(
        "2Surf_aOH-0.5 + 3H+ + PO4-3 = Surf_a2HPO4-1 + 2H2O",
        (20, 40),
        (-2, 0),
        True,
        0,
        -5,
        -1,
    )

    surface_b.add_surface(
        "Surf_b", "Surf_bOH-0.5", 6.97e-4, 350, 1, 0.74, 0.93, 0.001, 1, 1
    )
    surface_b.add_reactions(
        "Surf_bOH-0.5  + H+ = Surf_bOH2+0.5", 8.7, 0, True, 1, -5, -1
    )
    surface_b.add_reactions(
        "Surf_bOH-0.5 + K+  = Surf_bOHK+0.5", -1.16, 1, True, 1, -5, -1
    )
    surface_b.add_reactions(
        "Surf_bOH-0.5 + H+ + NO3- = Surf_bOH2NO3-0.5",
        7.74,
        -1,
        True,
        0,
        -5,
        -1,
    )

    titration = main_cal.Adsorption("CDMUSIC")
    titration.species_definition(database, "")
    titration.initial_solution(
        [0.5, 0.1, 0.01],
        initial_pH=7,
        cation="K",
        anion="N(5)",
        metal={"H3PO4": 6e-4},
    )
    titration.add_surface(surface_a)
    titration.add_surface(surface_b)
    titration.selected_output({"totals": "P"})
    titration.set_type_acid(type_base="KOH", type_acid="HNO3")
    titration.get_bounds()
    return data, titration


DATA, TITRATION = build_problem()
EXPERIMENTS = list(
    ParameterGrid(
        {
            "popsize": POPSIZES,
            "run_id": list(range(REPEATS_PER_POPSIZE)),
        }
    )
)


def run_single_experiment(parameters):
    popsize = parameters["popsize"]
    run_id = parameters["run_id"]
    seed = (run_id + 1) * RANDOM_SEED_MULTIPLIER
    objective_args = (
        DATA.iloc[:, 1].values,
        DATA.groupby("IS", sort=False),
        "",
        TITRATION,
    )
    start_time = time.perf_counter()

    try:
        de_result = de_opt(
            main_cal.advanced_fun_auto,
            bounds=np.asarray(TITRATION.bounds),
            args=objective_args,
            strategy="best1exp",
            init="halton",
            recombination=0.9,
            popsize=popsize,
            rng=seed,
            polish=False,
        )
        polish_result = optimize.minimize(
            main_cal.advanced_fun_auto,
            bounds=np.asarray(TITRATION.bounds),
            x0=de_result.x,
            args=objective_args,
            method="Nelder-Mead",
            options={"adaptive": True},
        )
        result = (
            polish_result
            if polish_result.success and polish_result.fun < de_result.fun
            else de_result
        )
        polish_nfev = polish_result.nfev
        return {
            "popsize": popsize,
            "population_members": popsize * len(TITRATION.bounds),
            "run_id": run_id,
            "seed": seed,
            "de_nfev": de_result.nfev,
            "de_nit": de_result.nit,
            "polish_nfev": polish_nfev,
            "total_nfev": de_result.nfev + polish_nfev,
            "de_fun": de_result.fun,
            "fun": result.fun,
            "time": time.perf_counter() - start_time,
            "error": None,
        }
    except Exception as error:
        return {
            "popsize": popsize,
            "population_members": popsize * len(TITRATION.bounds),
            "run_id": run_id,
            "seed": seed,
            "de_nfev": np.nan,
            "de_nit": np.nan,
            "polish_nfev": np.nan,
            "total_nfev": np.nan,
            "de_fun": np.nan,
            "fun": np.nan,
            "time": time.perf_counter() - start_time,
            "error": str(error),
        }
    finally:
        main_cal.close_cached_iphreeqc()


def summarize_results(results):
    raw = pd.DataFrame(results).sort_values(["popsize", "run_id"])
    summary = raw.groupby("popsize", as_index=False).agg(
        runs=("run_id", "count"),
        successes=("fun", "count"),
        population_members=("population_members", "first"),
        fun_mean=("fun", "mean"),
        fun_std=("fun", "std"),
        fun_min=("fun", "min"),
        fun_max=("fun", "max"),
        de_nfev_mean=("de_nfev", "mean"),
        total_nfev_mean=("total_nfev", "mean"),
        time_mean=("time", "mean"),
        time_std=("time", "std"),
    )
    summary["success_rate"] = summary["successes"] / summary["runs"]
    return raw, summary


if __name__ == "__main__":
    experiment_results = []
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [
            executor.submit(run_single_experiment, parameters)
            for parameters in EXPERIMENTS
        ]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="PO4 popsize test"
        ):
            experiment_results.append(future.result())

    raw_results, statistical_summary = summarize_results(experiment_results)
    raw_path = TEST_DIR / "de_popsize_raw_results_50_runs.csv"
    summary_path = TEST_DIR / "de_popsize_statistical_summary.csv"
    raw_results.to_csv(raw_path, index=False)
    statistical_summary.to_csv(summary_path, index=False)
    print(f"Raw results written to {raw_path}")
    print(f"Statistical summary written to {summary_path}")
