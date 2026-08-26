"""TPE/Bayesian-style search for BAC CCM DE parameters.

This searches the same finite parameter choices as bac_ccm_test_new.py, but
uses Optuna's TPE sampler instead of evaluating the full Cartesian grid. The
main process asks Optuna for a small batch of configurations, worker processes
run the independent DE experiments, and the results are then told back to the
study. This keeps IPhreeqc instances process-local and avoids thread races.
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

_script_file = globals().get("__file__")
_package_override = os.environ.get("PHREEFIT_BAC_PACKAGE_ROOT")
if _package_override:
    SCRIPT_DIR = Path(_package_override).expanduser().resolve()
elif _script_file:
    SCRIPT_DIR = Path(_script_file).resolve().parent
else:
    SCRIPT_DIR = Path.cwd().resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bac_ccm_test_new as grid  # noqa: E402

from scipy.optimize import differential_evolution  # noqa: E402


MUTATION_CHOICES = tuple(grid.mutation_label(item) for item in grid.MUTATIONS)
DEFAULT_TRIALS = 80
DEFAULT_STARTUP_TRIALS = 20
DEFAULT_WORKERS = 8
DEFAULT_CONFIRM_TOP = 10
DEFAULT_CONFIRM_REPEATS = 3
PENALTY = 1.0e12


def parse_mutation(label: str) -> tuple[float, float]:
    lower, upper = label.split(":", 1)
    return float(lower), float(upper)


def config_from_trial(trial) -> dict:
    return {
        "strategy": trial.suggest_categorical("strategy", list(grid.STRATEGIES)),
        "init": trial.suggest_categorical("init", list(grid.INITIALIZATIONS)),
        "recombination": trial.suggest_categorical(
            "recombination", list(grid.RECOMBINATIONS)
        ),
        "popsize": trial.suggest_categorical("popsize", list(grid.POPSIZES)),
        "mutation": trial.suggest_categorical("mutation", list(MUTATION_CHOICES)),
    }


def config_id(config: dict) -> str:
    return "|".join(
        (
            str(config["strategy"]),
            str(config["init"]),
            f"{float(config['recombination']):g}",
            str(config["popsize"]),
            str(config["mutation"]),
        )
    )


def run_de(config: dict, seed: int, maxiter: int) -> dict:
    """Run one independent DE experiment in a worker process."""
    data, titration = grid.build_problem()
    started = time.perf_counter()
    mutation = parse_mutation(config["mutation"])
    row = {
        **config,
        "mutation": config["mutation"],
        "seed": seed,
        "population_members": int(config["popsize"] * len(titration.bounds)),
    }
    try:
        random_argument = {grid._DE_RANDOM_KEYWORD: seed}
        result = differential_evolution(
            grid.main_cal.proto_fun,
            bounds=np.asarray(titration.bounds),
            args=(data[:, 0], titration, True),
            strategy=config["strategy"],
            init=config["init"],
            recombination=float(config["recombination"]),
            popsize=int(config["popsize"]),
            mutation=mutation,
            maxiter=maxiter,
            polish=False,
            workers=1,
            updating="immediate",
            **random_argument,
        )
        row.update(
            {
                "fun": float(result.fun),
                "nfev": int(result.nfev),
                "nit": int(result.nit),
                "elapsed_seconds": time.perf_counter() - started,
                "error": "",
            }
        )
    except Exception as error:
        row.update(
            {
                "fun": PENALTY,
                "nfev": -1,
                "nit": -1,
                "elapsed_seconds": time.perf_counter() - started,
                "error": str(error).replace("\n", "\\n"),
            }
        )
    finally:
        grid.main_cal.close_cached_iphreeqc()
    return row


def run_batch(tasks: list[tuple[object, dict, int, int]], workers: int) -> list[tuple]:
    """Run a bounded batch and return (Optuna trial, value, result row)."""
    if workers == 1:
        return [
            (trial, (row := run_de(config, seed, maxiter))["fun"], row)
            for trial, config, seed, maxiter in tasks
        ]

    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_de, config, seed, maxiter): (trial, config)
            for trial, config, seed, maxiter in tasks
        }
        pending = set(futures)
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                trial, config = futures[future]
                row = future.result()
                results.append((trial, row["fun"], row))
    return results


def trial_rows(study) -> list[dict]:
    rows = []
    for trial in study.trials:
        if trial.state.name != "COMPLETE":
            continue
        row = {
            "trial_number": trial.number,
            "value": trial.value,
            "state": trial.state.name,
            "strategy": trial.params.get("strategy"),
            "init": trial.params.get("init"),
            "recombination": trial.params.get("recombination"),
            "popsize": trial.params.get("popsize"),
            "mutation": trial.params.get("mutation"),
        }
        row.update(trial.user_attrs)
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def confirm_top(
    study, top_count: int, repeats: int, workers: int, maxiter: int
) -> list[dict]:
    completed = [t for t in study.trials if t.state.name == "COMPLETE"]
    unique = {}
    for trial in sorted(completed, key=lambda item: item.value):
        config = dict(trial.params)
        unique.setdefault(config_id(config), config)
    selected = list(unique.values())[:top_count]
    tasks = []
    for config in selected:
        for repeat in range(repeats):
            tasks.append(
                (None, config, (repeat + 1) * grid.RANDOM_SEED_MULTIPLIER, maxiter)
            )
    rows = []
    for _, _, row in run_batch(tasks, workers):
        rows.append(row)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--startup-trials", type=int, default=DEFAULT_STARTUP_TRIALS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--maxiter", type=int, default=1000)
    parser.add_argument("--confirm-top", type=int, default=DEFAULT_CONFIRM_TOP)
    parser.add_argument("--confirm-repeats", type=int, default=DEFAULT_CONFIRM_REPEATS)
    parser.add_argument(
        "--study",
        default="bac_ccm_tpe",
        help="Optuna study name stored in the SQLite database.",
    )
    parser.add_argument(
        "--database", type=Path, default=SCRIPT_DIR / "bac_ccm_tpe.db"
    )
    parser.add_argument(
        "--trials-output", type=Path, default=SCRIPT_DIR / "bac_ccm_tpe_trials.csv"
    )
    parser.add_argument(
        "--confirm-output",
        type=Path,
        default=SCRIPT_DIR / "bac_ccm_tpe_confirmation.csv",
    )
    parser.add_argument("--seed", type=int, default=20260820)
    parser.add_argument("--fresh", action="store_true")
    return parser.parse_args()


def main() -> None:
    try:
        import optuna
    except ImportError as error:
        raise SystemExit(
            "Optuna is required. Install it with: python -m pip install optuna"
        ) from error

    args = parse_args()
    if min(args.trials, args.startup_trials, args.workers, args.maxiter) < 1:
        raise ValueError("trials, startup-trials, workers, and maxiter must be positive")
    if args.confirm_top < 0 or args.confirm_repeats < 1:
        raise ValueError("confirm-top must be nonnegative and confirm-repeats positive")
    args.database = args.database.resolve()
    args.trials_output = args.trials_output.resolve()
    args.confirm_output = args.confirm_output.resolve()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.trials_output.parent.mkdir(parents=True, exist_ok=True)
    args.confirm_output.parent.mkdir(parents=True, exist_ok=True)
    if args.fresh and args.database.exists():
        raise FileExistsError(args.database)

    storage = f"sqlite:///{args.database.as_posix()}"
    sampler = optuna.samplers.TPESampler(
        seed=args.seed, n_startup_trials=args.startup_trials
    )
    study = optuna.create_study(
        study_name=args.study,
        storage=storage,
        load_if_exists=True,
        direction="minimize",
        sampler=sampler,
    )
    completed_count = len(
        [trial for trial in study.trials if trial.state.name == "COMPLETE"]
    )
    print(f"IPhreeqc library: {os.environ['PHREEFIT_IPHREEQC_LIBRARY']}")
    print(f"Optuna study: {args.study}")
    print(f"Completed trials: {completed_count}; target: {args.trials}")

    while completed_count < args.trials:
        batch_size = min(args.workers, args.trials - completed_count)
        tasks = []
        for _ in range(batch_size):
            trial = study.ask()
            config = config_from_trial(trial)
            seed = 100000 + trial.number
            tasks.append((trial, config, seed, args.maxiter))
        for trial, value, row in run_batch(tasks, args.workers):
            trial.set_user_attr("elapsed_seconds", row["elapsed_seconds"])
            trial.set_user_attr("nfev", row["nfev"])
            trial.set_user_attr("nit", row["nit"])
            trial.set_user_attr("error", row["error"])
            study.tell(trial, float(value))
            completed_count += 1
            print(
                f"trial {trial.number}: value={value:.8g}, "
                f"config={config_id(row)}, elapsed={row['elapsed_seconds']:.2f}s"
            )
        write_csv(args.trials_output, trial_rows(study))

    top = study.best_trial
    print(f"Best value: {top.value:.8g}")
    print(f"Best parameters: {json.dumps(top.params, ensure_ascii=False)}")
    write_csv(args.trials_output, trial_rows(study))
    if args.confirm_top:
        confirmations = confirm_top(
            study,
            args.confirm_top,
            args.confirm_repeats,
            args.workers,
            args.maxiter,
        )
        write_csv(args.confirm_output, confirmations)
        print(f"Confirmation results: {args.confirm_output}")
    print(f"Trial results: {args.trials_output}")
    print(f"Optuna database: {args.database}")


if __name__ == "__main__":
    main()
