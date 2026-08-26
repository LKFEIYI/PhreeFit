"""Server-ready differential-evolution grid search for the BAC CCM model.

The grid keeps the variables from ``bac_ccm_test.py`` and adds ``popsize``
and ``mutation``.  The bundled optimized IPhreeqc 3.8.6 library and bundled
``src_new.main_cal`` are selected relative to this file, so the package can be
run from any working directory.
"""

from __future__ import annotations

import argparse
import atexit
import csv
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import product
import inspect
import os
from pathlib import Path
import sys
import time

# Each outer process runs one serial SciPy optimizer. Prevent native numerical
# libraries from creating another layer of threads on the server.
for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_variable] = "1"


_script_file = globals().get("__file__")
_package_override = os.environ.get("PHREEFIT_BAC_PACKAGE_ROOT")
if _package_override:
    SCRIPT_DIR = Path(_package_override).expanduser().resolve()
elif _script_file:
    SCRIPT_DIR = Path(_script_file).resolve().parent
else:
    # exec(), notebooks, and some cluster schedulers do not define __file__.
    # In that mode the process must be started from the extracted package
    # directory (or PHREEFIT_BAC_PACKAGE_ROOT must be set).
    SCRIPT_DIR = Path.cwd().resolve()
PACKAGE_ROOT = SCRIPT_DIR
if not (PACKAGE_ROOT / "src_new" / "main_cal.py").is_file():
    # Development-tree layout: test/bac/bac_ccm_test_new.py
    PACKAGE_ROOT = SCRIPT_DIR.parents[1]

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


def bundled_library() -> Path:
    if sys.platform == "darwin":
        name = "libiphreeqc-3.8.6.dylib"
    elif sys.platform == "win32":
        name = "IPhreeqc-3.8.6.dll"
    elif sys.platform.startswith("linux"):
        name = "libiphreeqc-3.8.6.so"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")
    library = PACKAGE_ROOT / "lib" / name
    if not library.is_file():
        # Development-tree layout.
        library = PACKAGE_ROOT / "packaging" / "lib" / name
    if not library.is_file():
        raise FileNotFoundError(
            f"No bundled IPhreeqc library for {sys.platform}: expected {library}. "
            "This package currently contains macOS arm64 and Windows x64 builds."
        )
    return library.resolve()


# Select the new library before importing main_cal. An explicitly configured
# valid library is preserved, which also permits a separately built Linux .so.
_configured_library = os.environ.get("PHREEFIT_IPHREEQC_LIBRARY")
if not _configured_library or not Path(_configured_library).is_file():
    os.environ["PHREEFIT_IPHREEQC_LIBRARY"] = str(bundled_library())

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from tqdm import tqdm

from src_new import main_cal

atexit.register(main_cal.close_cached_iphreeqc)

_DE_RANDOM_KEYWORD = (
    "rng"
    if "rng" in inspect.signature(differential_evolution).parameters
    else "seed"
)


STRATEGIES = (
    "best1bin",
    "best1exp",
    "rand1bin",
    "rand1exp",
    "rand2bin",
    "rand2exp",
    "randtobest1bin",
    "randtobest1exp",
    "currenttobest1bin",
    "currenttobest1exp",
    "best2exp",
    "best2bin",
)
INITIALIZATIONS = ("latinhypercube", "sobol", "halton", "random")
RECOMBINATIONS = (0.7, 0.8, 0.9)
POPSIZES = (5, 8, 10, 15, 20)
MUTATIONS = ((0.3, 0.8), (0.5, 1.0), (0.6, 1.2))
DEFAULT_REPEATS = 50
DEFAULT_WORKERS = 2
RANDOM_SEED_MULTIPLIER = 42

RESULT_FIELDS = (
    "experiment_id",
    "strategy",
    "init",
    "recombination",
    "popsize",
    "mutation",
    "run_id",
    "seed",
    "population_members",
    "nfev",
    "nit",
    "fun",
    "elapsed_seconds",
    "error",
)

_worker_data = None
_worker_titration = None


def build_problem():
    database = (SCRIPT_DIR / "simple_davies_for_titration.dat").read_text(
        encoding="UTF-8"
    )
    data = np.loadtxt(SCRIPT_DIR / "bacteria.csv", delimiter=",", skiprows=1)

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
    surface_c.add_surface(
        "Surf_c", "Surf_cH", (0, 0.01), 140, 0.9705, (0, 5), 1, 0.001, 1, 1
    )
    surface_c.add_reactions(
        "Surf_cH = Surf_c- + H+", (-11, -2), 1, True, 1, -5, -1
    )

    titration = main_cal.Adsorption("CCM")
    titration.species_definition(database, "")
    titration.initial_solution(
        [0.1], initial_pH=2.449, cation="Na", anion="Cl", metal={}
    )
    titration.add_surface(surface_a)
    titration.add_surface(surface_b)
    titration.add_surface(surface_c)
    titration.selected_output({})
    titration.set_type_acid(type_base="NaOH", type_acid="HNO3")
    titration.mix_solution(type_solution="dissolution", base_mass=0.993)
    titration.mix_action(initial_volume=6.509, mix_volume=data[:, 1])
    titration.get_bounds()
    return data, titration


def worker_problem():
    global _worker_data, _worker_titration
    if _worker_titration is None:
        _worker_data, _worker_titration = build_problem()
    return _worker_data, _worker_titration


def mutation_label(mutation: tuple[float, float]) -> str:
    return f"{mutation[0]:g}:{mutation[1]:g}"


def experiment_id(experiment: tuple) -> str:
    strategy, init, recombination, popsize, mutation, run_id, _ = experiment
    return "|".join(
        (
            strategy,
            init,
            f"{recombination:g}",
            str(popsize),
            mutation_label(mutation),
            str(run_id),
        )
    )


def run_single_experiment(experiment: tuple) -> dict:
    strategy, init, recombination, popsize, mutation, run_id, maxiter = experiment
    seed = (run_id + 1) * RANDOM_SEED_MULTIPLIER
    data, titration = worker_problem()
    started = time.perf_counter()
    row = {
        "experiment_id": experiment_id(experiment),
        "strategy": strategy,
        "init": init,
        "recombination": recombination,
        "popsize": popsize,
        "mutation": mutation_label(mutation),
        "run_id": run_id,
        "seed": seed,
        "population_members": popsize * len(titration.bounds),
    }
    try:
        de_random = {_DE_RANDOM_KEYWORD: seed}
        result = differential_evolution(
            main_cal.proto_fun,
            bounds=np.asarray(titration.bounds),
            args=(data[:, 0], titration, True),
            strategy=strategy,
            init=init,
            recombination=recombination,
            popsize=popsize,
            mutation=mutation,
            maxiter=maxiter,
            polish=False,
            workers=1,
            updating="immediate",
            **de_random,
        )
        row.update(
            {
                "nfev": int(result.nfev),
                "nit": int(result.nit),
                "fun": float(result.fun),
                "elapsed_seconds": time.perf_counter() - started,
                "error": "",
            }
        )
    except Exception as error:
        row.update(
            {
                "nfev": -1,
                "nit": -1,
                "fun": np.inf,
                "elapsed_seconds": time.perf_counter() - started,
                "error": str(error).replace("\n", "\\n"),
            }
        )
    return row


def generate_experiments(repeats: int, maxiter: int):
    return [
        (*values, run_id, maxiter)
        for values in product(
            STRATEGIES,
            INITIALIZATIONS,
            RECOMBINATIONS,
            POPSIZES,
            MUTATIONS,
        )
        for run_id in range(repeats)
    ]


def completed_ids(output: Path) -> set[str]:
    if not output.is_file() or output.stat().st_size == 0:
        return set()
    with output.open("r", encoding="utf-8", newline="") as stream:
        return {row["experiment_id"] for row in csv.DictReader(stream)}


def write_summary(raw_output: Path, summary_output: Path) -> None:
    raw = pd.read_csv(raw_output)
    raw["successful"] = raw["error"].fillna("").eq("")
    successful = raw[raw["successful"]].copy()
    group_columns = [
        "strategy",
        "init",
        "recombination",
        "popsize",
        "mutation",
    ]
    attempts = raw.groupby(group_columns, as_index=False).agg(
        runs=("run_id", "count"),
        successes=("successful", "sum"),
        attempt_time_mean=("elapsed_seconds", "mean"),
        attempt_time_std=("elapsed_seconds", "std"),
    )
    success_stats = successful.groupby(group_columns, as_index=False).agg(
        fun_mean=("fun", "mean"),
        fun_std=("fun", "std"),
        fun_min=("fun", "min"),
        fun_median=("fun", "median"),
        nfev_mean=("nfev", "mean"),
        nit_mean=("nit", "mean"),
        successful_time_mean=("elapsed_seconds", "mean"),
    )
    summary = attempts.merge(success_stats, on=group_columns, how="left")
    summary["success_rate"] = summary["successes"] / summary["runs"]
    summary.sort_values(
        ["fun_mean", "attempt_time_mean"], na_position="last"
    ).to_csv(summary_output, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--maxiter", type=int, default=1000)
    parser.add_argument(
        "--output", type=Path, default=SCRIPT_DIR / "bac_ccm_grid_raw.csv"
    )
    parser.add_argument(
        "--summary", type=Path, default=SCRIPT_DIR / "bac_ccm_grid_summary.csv"
    )
    parser.add_argument(
        "--library",
        type=Path,
        help="Optional explicit IPhreeqc library; defaults to the bundled new library.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Refuse to append to an existing output instead of resuming it.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Run only the first N pending experiments (useful for a smoke test).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.workers < 1 or args.repeats < 1 or args.maxiter < 1:
        raise ValueError("workers, repeats, and maxiter must be positive")
    if args.library:
        library = args.library.resolve()
        if not library.is_file():
            raise FileNotFoundError(library)
        os.environ["PHREEFIT_IPHREEQC_LIBRARY"] = str(library)

    output = args.output.resolve()
    summary = args.summary.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.parent.mkdir(parents=True, exist_ok=True)
    if args.fresh and output.exists():
        raise FileExistsError(f"Output already exists: {output}")

    experiments = generate_experiments(args.repeats, args.maxiter)
    done = completed_ids(output)
    pending = [item for item in experiments if experiment_id(item) not in done]
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("limit must be positive")
        pending = pending[: args.limit]
    print(f"IPhreeqc library: {os.environ['PHREEFIT_IPHREEQC_LIBRARY']}")
    print(f"Grid experiments: {len(experiments):,}")
    print(f"Already completed: {len(done):,}")
    print(f"Pending: {len(pending):,}; outer workers: {args.workers}")
    if not pending:
        write_summary(output, summary)
        print(f"Nothing to run. Summary refreshed: {summary}")
        return

    needs_header = not output.exists() or output.stat().st_size == 0
    with output.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=RESULT_FIELDS)
        if needs_header:
            writer.writeheader()
            stream.flush()
        if args.workers == 1:
            iterator = map(run_single_experiment, pending)
            for index, result in enumerate(
                tqdm(iterator, total=len(pending), desc="BAC CCM grid", unit="run"),
                start=1,
            ):
                writer.writerow(result)
                if index % 10 == 0:
                    stream.flush()
        else:
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                # Keep only a small queue of futures. Unlike executor.map,
                # this reports whichever worker finishes first, so a slow
                # first grid point cannot make the progress bar look idle.
                pending_iterator = iter(pending)
                futures = {
                    executor.submit(run_single_experiment, next(pending_iterator))
                    for _ in range(min(args.workers * 2, len(pending)))
                }
                with tqdm(
                    total=len(pending), desc="BAC CCM grid", unit="run"
                ) as progress:
                    index = 0
                    while futures:
                        done_futures, futures = wait(
                            futures, return_when=FIRST_COMPLETED
                        )
                        for future in done_futures:
                            result = future.result()
                            writer.writerow(result)
                            stream.flush()
                            progress.update(1)
                            index += 1
                            try:
                                next_item = next(pending_iterator)
                            except StopIteration:
                                continue
                            futures.add(
                                executor.submit(run_single_experiment, next_item)
                            )
        stream.flush()

    write_summary(output, summary)
    print(f"Raw results: {output}")
    print(f"Summary:     {summary}")


if __name__ == "__main__":
    main()
