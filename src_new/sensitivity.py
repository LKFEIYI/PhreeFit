"""Local and Morris sensitivity calculations for configured PhreeFit models."""

from dataclasses import dataclass
from datetime import datetime
import json
import os
import re
import tempfile

import numpy as np

from . import main_cal as mc


@dataclass
class SensitivityResult:
    task: str
    mode: str
    model: str
    timestamp: str
    x_label: str
    response_label: str
    x_values: np.ndarray
    baseline_response: np.ndarray
    parameters: list
    baseline_parameters: np.ndarray
    raw_sensitivity: np.ndarray
    normalized_sensitivity: np.ndarray
    importance: np.ndarray
    correlation: np.ndarray
    perturbation_percent: float
    method: str = "local"
    trajectories: int = 0
    levels: int = 0
    random_seed: int = 0
    morris_mu: np.ndarray = None
    morris_mu_star: np.ndarray = None
    morris_sigma: np.ndarray = None
    elementary_effects: np.ndarray = None
    json_path: str = ""


def build_parameter_specs(problem):
    """Describe fitted parameters in exactly the order used by get_bounds/set_para."""
    specs = []

    def add(value, initial, name, kind, surface, reaction=None):
        if not isinstance(value, tuple):
            return
        specs.append({
            "name": name,
            "kind": kind,
            "surface": surface,
            "reaction": reaction,
            "initial": initial,
            "lower": value[0],
            "upper": value[1],
        })

    for surface in problem.surface:
        add(
            surface.surface_sites,
            surface.sfinitial[0],
            f"{surface.surface_name} / Sites",
            "Sites",
            surface.surface_name,
        )
        for reaction, values in surface.surface_reactions.items():
            add(
                values[0],
                values[4],
                f"{surface.surface_name} / {reaction} / log_k",
                "log_k",
                surface.surface_name,
                reaction,
            )
            if problem.p_type == "CDMUSIC":
                add(
                    values[1],
                    values[5],
                    f"{surface.surface_name} / {reaction} / z1",
                    "z1",
                    surface.surface_name,
                    reaction,
                )
        if problem.p_type == "CCM":
            add(
                surface.surface_C1,
                surface.sfinitial[1],
                f"{surface.surface_name} / C1",
                "C1",
                surface.surface_name,
            )
        elif problem.p_type == "CDMUSIC":
            add(
                surface.surface_C1,
                surface.sfinitial[1],
                f"{surface.surface_name} / C1",
                "C1",
                surface.surface_name,
            )
            add(
                surface.surface_C2,
                surface.sfinitial[2],
                f"{surface.surface_name} / C2",
                "C2",
                surface.surface_name,
            )
    if len(specs) != len(problem.bounds):
        raise ValueError("Sensitivity parameter mapping does not match model bounds.")
    return specs


def _evaluate_response(problem, parameters, mix_mode, ph_list=None, eq_phase=None):
    problem.set_para(parameters)
    if mix_mode == 0:
        problem.create_script(mix=True)
        return np.asarray(mc.run_phreeqc(problem), dtype=float)
    if mix_mode == 2:
        problem.eq_ph(
            ph_list=ph_list,
            eq_phase=eq_phase or "",
            ph_sep=None,
            auto_p=True,
        )
    problem.create_script(mix=False)
    return np.asarray(mc.run_phreeqc_ad(problem), dtype=float)


def _parameter_correlation(normalized_sensitivity):
    matrix = np.asarray(normalized_sensitivity, dtype=float)
    parameter_count = matrix.shape[0]
    if parameter_count == 0:
        return np.empty((0, 0), dtype=float)
    if matrix.shape[1] < 2:
        return np.eye(parameter_count, dtype=float)
    centered = matrix - np.mean(matrix, axis=1, keepdims=True)
    norms = np.linalg.norm(centered, axis=1)
    denominator = np.outer(norms, norms)
    correlation = np.divide(
        centered @ centered.T,
        denominator,
        out=np.zeros((parameter_count, parameter_count), dtype=float),
        where=denominator > 0,
    )
    for index, norm in enumerate(norms):
        correlation[index, index] = 1.0 if norm > 0 else 0.0
    return np.clip(correlation, -1.0, 1.0)


def estimate_parameter_uncertainty(
        problem,
        optimal_parameters,
        experimental_data,
        baseline_response,
        bounds,
        error_list,
        mix_mode,
        ph_list=None,
        eq_phase=None,
        relative_step=1e-3,
        stop_requested=None):
    """Estimate one-standard-deviation parameter uncertainty from a numerical Jacobian."""
    parameters = np.asarray(optimal_parameters, dtype=float)
    experimental = np.asarray(experimental_data, dtype=float)
    baseline = np.asarray(baseline_response, dtype=float)
    parameter_count = len(parameters)
    unavailable = np.full(parameter_count, np.nan, dtype=float)
    if parameter_count == 0 or len(bounds) != parameter_count:
        return unavailable
    if baseline.shape != experimental.shape or baseline.ndim != 1:
        return unavailable
    degrees_of_freedom = len(experimental) - parameter_count
    if degrees_of_freedom <= 0:
        return unavailable

    errors = np.abs(np.asarray(error_list, dtype=float))
    if errors.shape != experimental.shape:
        return unavailable
    valid_errors = errors[np.isfinite(errors) & (errors > 0)]
    if valid_errors.size:
        error_floor = max(float(np.median(valid_errors)) * 1e-6, np.finfo(float).eps)
    else:
        response_scale = max(float(np.max(np.abs(experimental))), 1.0)
        error_floor = response_scale * 1e-6
    errors = np.where(np.isfinite(errors) & (errors > error_floor), errors, error_floor)

    def check_cancelled():
        if stop_requested is not None and stop_requested():
            raise mc.OptimizationCancelled("Terminated during uncertainty estimation")

    jacobian = np.empty((len(experimental), parameter_count), dtype=float)
    try:
        for parameter_index, bound in enumerate(bounds):
            check_cancelled()
            lower, upper = float(bound[0]), float(bound[1])
            center = float(parameters[parameter_index])
            span = upper - lower
            if not np.isfinite(span) or span <= 0 or center < lower or center > upper:
                return unavailable
            step = max(span * float(relative_step), abs(center) * 1e-6, 1e-12)
            low_value = max(lower, center - step)
            high_value = min(upper, center + step)
            if high_value <= low_value:
                return unavailable

            if low_value == center:
                low_response = baseline
            else:
                low_parameters = parameters.copy()
                low_parameters[parameter_index] = low_value
                low_response = _evaluate_response(
                    problem, low_parameters, mix_mode, ph_list=ph_list, eq_phase=eq_phase
                )
            check_cancelled()
            if high_value == center:
                high_response = baseline
            else:
                high_parameters = parameters.copy()
                high_parameters[parameter_index] = high_value
                high_response = _evaluate_response(
                    problem, high_parameters, mix_mode, ph_list=ph_list, eq_phase=eq_phase
                )
            derivative = (high_response - low_response) / (high_value - low_value)
            jacobian[:, parameter_index] = derivative / errors

        if not np.all(np.isfinite(jacobian)):
            return unavailable
        weighted_residual = (baseline - experimental) / errors
        residual_variance = float(weighted_residual @ weighted_residual) / degrees_of_freedom
        information = jacobian.T @ jacobian
        singular_values = np.linalg.svd(information, compute_uv=False)
        if not singular_values.size or singular_values[0] <= 0:
            return unavailable
        tolerance = max(information.shape) * np.finfo(float).eps * singular_values[0]
        if int(np.count_nonzero(singular_values > tolerance)) < parameter_count:
            return unavailable
        covariance = residual_variance * np.linalg.pinv(information)
        diagonal = np.diag(covariance)
        if np.any(~np.isfinite(diagonal)) or np.any(diagonal < 0):
            return unavailable
        return np.sqrt(diagonal)
    finally:
        problem.set_para(parameters)


def calculate_local_sensitivity(
        problem,
        baseline_parameters,
        selected_indexes,
        perturbation_percent,
        mix_mode,
        x_values,
        x_label,
        response_label,
        task,
        mode_label=None,
        ph_list=None,
        eq_phase=None,
        stop_requested=None,
        progress=None,
        parameter_specs=None):
    """Calculate bound-aware, normalized finite-difference sensitivities."""
    baseline = np.asarray(baseline_parameters, dtype=float).copy()
    parameter_specs = parameter_specs or build_parameter_specs(problem)
    if len(baseline) != len(parameter_specs):
        raise ValueError("The sensitivity baseline does not match the current model parameters.")
    selected_indexes = list(dict.fromkeys(int(index) for index in selected_indexes))
    if not selected_indexes:
        raise ValueError("Select at least one parameter for sensitivity analysis.")
    if perturbation_percent <= 0:
        raise ValueError("Perturbation must be greater than zero.")

    def check_cancelled():
        if stop_requested is not None and stop_requested():
            raise mc.OptimizationCancelled("Sensitivity analysis cancelled by user")

    check_cancelled()
    baseline_response = _evaluate_response(
        problem, baseline, mix_mode, ph_list=ph_list, eq_phase=eq_phase
    )
    x_array = np.asarray(x_values, dtype=float)
    if len(x_array) != len(baseline_response):
        x_array = np.arange(len(baseline_response), dtype=float)
        x_label = "Data point"
    total_evaluations = 1 + 2 * len(selected_indexes)
    completed_evaluations = 1
    if progress is not None:
        progress(completed_evaluations, total_evaluations, "Baseline calculated")

    response_scale = float(np.ptp(baseline_response))
    if not np.isfinite(response_scale) or response_scale <= np.finfo(float).eps:
        response_scale = float(np.max(np.abs(baseline_response))) if baseline_response.size else 1.0
    response_scale = max(response_scale, np.finfo(float).eps)

    raw_rows = []
    normalized_rows = []
    selected_specs = []
    selected_baseline = []
    fraction = float(perturbation_percent) / 100.0
    for parameter_index in selected_indexes:
        check_cancelled()
        spec = dict(parameter_specs[parameter_index])
        lower = float(spec["lower"])
        upper = float(spec["upper"])
        center = float(baseline[parameter_index])
        span = upper - lower
        if not np.isfinite(span) or span <= 0:
            raise ValueError(f"Parameter has no usable range: {spec['name']}")
        if center < lower or center > upper:
            raise ValueError(f"Baseline is outside bounds: {spec['name']}")

        step = span * fraction
        low_value = max(lower, center - step)
        high_value = min(upper, center + step)
        if high_value <= low_value:
            raise ValueError(f"Unable to perturb parameter within bounds: {spec['name']}")

        if low_value == center:
            low_response = baseline_response
        else:
            low_parameters = baseline.copy()
            low_parameters[parameter_index] = low_value
            low_response = _evaluate_response(
                problem, low_parameters, mix_mode, ph_list=ph_list, eq_phase=eq_phase
            )
        completed_evaluations += 1
        if progress is not None:
            progress(completed_evaluations, total_evaluations, spec["name"] + " (low)")
        check_cancelled()
        if high_value == center:
            high_response = baseline_response
        else:
            high_parameters = baseline.copy()
            high_parameters[parameter_index] = high_value
            high_response = _evaluate_response(
                problem, high_parameters, mix_mode, ph_list=ph_list, eq_phase=eq_phase
            )
        completed_evaluations += 1
        if progress is not None:
            progress(completed_evaluations, total_evaluations, spec["name"] + " (high)")

        derivative = (high_response - low_response) / (high_value - low_value)
        normalized = derivative * span / response_scale
        raw_rows.append(derivative)
        normalized_rows.append(normalized)
        spec["baseline"] = center
        spec["perturbation_low"] = low_value
        spec["perturbation_high"] = high_value
        selected_specs.append(spec)
        selected_baseline.append(center)

    raw_matrix = np.asarray(raw_rows, dtype=float)
    normalized_matrix = np.asarray(normalized_rows, dtype=float)
    importance = np.sqrt(np.mean(np.square(normalized_matrix), axis=1))
    correlation = _parameter_correlation(normalized_matrix)
    return SensitivityResult(
        task=task or "(unnamed)",
        mode=mode_label or ("Titration" if mix_mode == 0 else "Advanced"),
        model=problem.p_type,
        timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
        x_label=x_label,
        response_label=response_label,
        x_values=x_array,
        baseline_response=baseline_response,
        parameters=selected_specs,
        baseline_parameters=np.asarray(selected_baseline, dtype=float),
        raw_sensitivity=raw_matrix,
        normalized_sensitivity=normalized_matrix,
        importance=importance,
        correlation=correlation,
        perturbation_percent=float(perturbation_percent),
        method="local",
    )


def calculate_morris_sensitivity(
        problem,
        baseline_parameters,
        selected_indexes,
        trajectories,
        levels,
        random_seed,
        mix_mode,
        x_values,
        x_label,
        response_label,
        task,
        mode_label=None,
        ph_list=None,
        eq_phase=None,
        stop_requested=None,
        progress=None,
        parameter_specs=None):
    """Calculate Morris elementary effects across the complete parameter bounds."""
    baseline = np.asarray(baseline_parameters, dtype=float).copy()
    parameter_specs = parameter_specs or build_parameter_specs(problem)
    if len(baseline) != len(parameter_specs):
        raise ValueError("The sensitivity baseline does not match the current model parameters.")
    selected_indexes = list(dict.fromkeys(int(index) for index in selected_indexes))
    if not selected_indexes:
        raise ValueError("Select at least one parameter for sensitivity analysis.")
    trajectories = int(trajectories)
    levels = int(levels)
    if trajectories < 2:
        raise ValueError("Morris analysis requires at least two trajectories.")
    if levels < 4 or levels % 2:
        raise ValueError("Morris grid levels must be an even number of at least four.")

    def check_cancelled():
        if stop_requested is not None and stop_requested():
            raise mc.OptimizationCancelled("Sensitivity analysis cancelled by user")

    for parameter_index in selected_indexes:
        spec = parameter_specs[parameter_index]
        lower = float(spec["lower"])
        upper = float(spec["upper"])
        if not np.isfinite(upper - lower) or upper <= lower:
            raise ValueError(f"Parameter has no usable range: {spec['name']}")

    check_cancelled()
    baseline_response = _evaluate_response(
        problem, baseline, mix_mode, ph_list=ph_list, eq_phase=eq_phase
    )
    x_array = np.asarray(x_values, dtype=float)
    if len(x_array) != len(baseline_response):
        x_array = np.arange(len(baseline_response), dtype=float)
        x_label = "Data point"
    response_scale = float(np.ptp(baseline_response))
    if not np.isfinite(response_scale) or response_scale <= np.finfo(float).eps:
        response_scale = float(np.max(np.abs(baseline_response))) if baseline_response.size else 1.0
    response_scale = max(response_scale, np.finfo(float).eps)

    parameter_count = len(selected_indexes)
    point_count = len(baseline_response)
    effects = np.empty((parameter_count, trajectories, point_count), dtype=float)
    rng = np.random.default_rng(int(random_seed))
    delta = levels / (2.0 * (levels - 1.0))
    grid = np.linspace(0.0, 1.0, levels)
    low_candidates = grid[grid <= 1.0 - delta + 1e-12]
    total_evaluations = 1 + trajectories * (parameter_count + 1)
    completed_evaluations = 1
    if progress is not None:
        progress(completed_evaluations, total_evaluations, "Baseline calculated")

    selected_specs = []
    selected_baseline = []
    for parameter_index in selected_indexes:
        spec = dict(parameter_specs[parameter_index])
        spec["baseline"] = float(baseline[parameter_index])
        selected_specs.append(spec)
        selected_baseline.append(float(baseline[parameter_index]))

    for trajectory_index in range(trajectories):
        check_cancelled()
        normalized_position = {}
        directions = {}
        trajectory_parameters = baseline.copy()
        for parameter_index in selected_indexes:
            low = float(rng.choice(low_candidates))
            direction = int(rng.choice((-1, 1)))
            normalized = low if direction > 0 else low + delta
            normalized_position[parameter_index] = normalized
            directions[parameter_index] = direction
            spec = parameter_specs[parameter_index]
            trajectory_parameters[parameter_index] = (
                float(spec["lower"])
                + normalized * (float(spec["upper"]) - float(spec["lower"]))
            )

        current_response = _evaluate_response(
            problem, trajectory_parameters, mix_mode, ph_list=ph_list, eq_phase=eq_phase
        )
        completed_evaluations += 1
        if progress is not None:
            progress(
                completed_evaluations,
                total_evaluations,
                f"Trajectory {trajectory_index + 1}/{trajectories}",
            )

        for parameter_index in rng.permutation(selected_indexes):
            check_cancelled()
            old_normalized = normalized_position[parameter_index]
            signed_delta = directions[parameter_index] * delta
            new_normalized = old_normalized + signed_delta
            next_parameters = trajectory_parameters.copy()
            spec = parameter_specs[parameter_index]
            next_parameters[parameter_index] = (
                float(spec["lower"])
                + new_normalized * (float(spec["upper"]) - float(spec["lower"]))
            )
            next_response = _evaluate_response(
                problem, next_parameters, mix_mode, ph_list=ph_list, eq_phase=eq_phase
            )
            local_index = selected_indexes.index(int(parameter_index))
            effects[local_index, trajectory_index] = (
                (next_response - current_response) / (signed_delta * response_scale)
            )
            normalized_position[parameter_index] = new_normalized
            trajectory_parameters = next_parameters
            current_response = next_response
            completed_evaluations += 1
            if progress is not None:
                progress(
                    completed_evaluations,
                    total_evaluations,
                    f"Trajectory {trajectory_index + 1}/{trajectories}: {spec['name']}",
                )

    mu_by_point = np.mean(effects, axis=1)
    mu_star_by_point = np.mean(np.abs(effects), axis=1)
    sigma_by_point = np.std(effects, axis=1, ddof=1)
    morris_mu = np.mean(mu_by_point, axis=1)
    morris_mu_star = np.mean(mu_star_by_point, axis=1)
    morris_sigma = np.mean(sigma_by_point, axis=1)
    return SensitivityResult(
        task=task or "(unnamed)",
        mode=mode_label or ("Titration" if mix_mode == 0 else "Advanced"),
        model=problem.p_type,
        timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
        x_label=x_label,
        response_label=response_label,
        x_values=x_array,
        baseline_response=baseline_response,
        parameters=selected_specs,
        baseline_parameters=np.asarray(selected_baseline, dtype=float),
        raw_sensitivity=mu_by_point,
        normalized_sensitivity=mu_star_by_point,
        importance=morris_mu_star,
        correlation=np.empty((0, 0), dtype=float),
        perturbation_percent=0.0,
        method="morris",
        trajectories=trajectories,
        levels=levels,
        random_seed=int(random_seed),
        morris_mu=morris_mu,
        morris_mu_star=morris_mu_star,
        morris_sigma=morris_sigma,
        elementary_effects=effects,
    )


def _safe_task_name(task):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (task or "sensitivity").strip())
    return cleaned.strip("._-") or "sensitivity"


def load_sensitivity_result(path):
    """Load sensitivity JSON written by result format version 1 or 2."""
    with open(path, "r", encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict) or payload.get("format") != "PhreeFit sensitivity":
        raise ValueError("The selected file is not a PhreeFit sensitivity result.")
    try:
        version = int(payload.get("version", 1))
    except (TypeError, ValueError) as error:
        raise ValueError("The sensitivity result has an invalid version.") from error
    if version not in (1, 2):
        raise ValueError(f"Unsupported sensitivity result version: {version}")

    method_value = str(payload.get("method", "local")).casefold()
    method = "morris" if method_value == "morris" else "local"
    parameters = payload.get("parameters")
    if not isinstance(parameters, list) or not parameters:
        raise ValueError("The sensitivity result contains no parameters.")
    local_data = payload.get("local") if isinstance(payload.get("local"), dict) else {}
    morris_data = payload.get("morris") if isinstance(payload.get("morris"), dict) else {}

    def array(name, fallback=None):
        value = payload.get(name, fallback)
        if value is None:
            value = []
        try:
            return np.asarray(value, dtype=float)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid numeric data in sensitivity field: {name}") from error

    raw = array("raw_sensitivity", local_data.get("raw_sensitivity", morris_data.get("mu_by_point")))
    normalized = array(
        "normalized_sensitivity",
        local_data.get("normalized_sensitivity", morris_data.get("mu_star_by_point")),
    )
    importance = array("importance", morris_data.get("mu_star"))
    parameter_count = len(parameters)
    if raw.ndim != 2 or normalized.ndim != 2:
        raise ValueError("Sensitivity matrices must be two-dimensional.")
    if raw.shape[0] != parameter_count or normalized.shape[0] != parameter_count:
        raise ValueError("Sensitivity matrices do not match the parameter list.")
    if importance.shape != (parameter_count,):
        raise ValueError("Sensitivity importance does not match the parameter list.")

    if method == "morris":
        morris_mu = array("morris.mu", morris_data.get("mu"))
        morris_mu_star = array("morris.mu_star", morris_data.get("mu_star"))
        morris_sigma = array("morris.sigma", morris_data.get("sigma"))
        elementary_effects = array(
            "morris.elementary_effects", morris_data.get("elementary_effects")
        )
        for name, values in (
            ("mu", morris_mu), ("mu_star", morris_mu_star), ("sigma", morris_sigma)
        ):
            if values.shape != (parameter_count,):
                raise ValueError(f"Morris {name} does not match the parameter list.")
        if (elementary_effects.ndim != 3
                or elementary_effects.shape[0] != parameter_count):
            raise ValueError("Morris elementary effects do not match the parameter list.")
    else:
        morris_mu = None
        morris_mu_star = None
        morris_sigma = None
        elementary_effects = None

    result = SensitivityResult(
        task=str(payload.get("task") or "(unnamed)"),
        mode=str(payload.get("mode") or "Unknown"),
        model=str(payload.get("model") or "Unknown"),
        timestamp=str(payload.get("timestamp") or ""),
        x_label=str(payload.get("x_label") or "Data point"),
        response_label=str(payload.get("response_label") or "Response"),
        x_values=array("x_values"),
        baseline_response=array("baseline_response"),
        parameters=parameters,
        baseline_parameters=array("baseline_parameters"),
        raw_sensitivity=raw,
        normalized_sensitivity=normalized,
        importance=importance,
        correlation=(
            array("correlation", local_data.get("correlation"))
            if method == "local" else np.empty((0, 0), dtype=float)
        ),
        perturbation_percent=float(
            local_data.get("perturbation_percent", payload.get("perturbation_percent", 0.0))
        ),
        method=method,
        trajectories=int(morris_data.get("trajectories", 0)),
        levels=int(morris_data.get("levels", 0)),
        random_seed=int(morris_data.get("random_seed", 0)),
        morris_mu=morris_mu,
        morris_mu_star=morris_mu_star,
        morris_sigma=morris_sigma,
        elementary_effects=elementary_effects,
        json_path=os.path.abspath(path),
    )
    if len(result.x_values) != raw.shape[1]:
        raise ValueError("Sensitivity x values do not match the result matrix.")
    if len(result.baseline_response) != raw.shape[1]:
        raise ValueError("Baseline response does not match the result matrix.")
    if method == "local" and result.correlation.shape != (parameter_count, parameter_count):
        raise ValueError("Sensitivity correlation does not match the parameter list.")
    return result


def _atomic_text_file(target, writer):
    directory = os.path.dirname(os.path.abspath(target))
    os.makedirs(directory, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=directory,
                prefix=".phreefit-sensitivity-", suffix=".tmp", delete=False) as output:
            temporary_path = output.name
            writer(output)
        os.replace(temporary_path, target)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def save_sensitivity_result(result, output_folder):
    """Save one complete JSON result in Output path."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = f"sensitivity_{_safe_task_name(result.task)}_{stamp}"
    json_path = os.path.join(output_folder, base_name + ".json")

    def write_json(output):
        payload = {
            "format": "PhreeFit sensitivity",
            "version": 2,
            "task": result.task,
            "timestamp": result.timestamp,
            "mode": result.mode,
            "model": result.model,
            "method": result.method,
            "x_label": result.x_label,
            "response_label": result.response_label,
            "x_values": result.x_values.tolist(),
            "baseline_response": result.baseline_response.tolist(),
            "parameters": result.parameters,
            "baseline_parameters": result.baseline_parameters.tolist(),
            "raw_sensitivity": result.raw_sensitivity.tolist(),
            "normalized_sensitivity": result.normalized_sensitivity.tolist(),
            "importance": result.importance.tolist(),
        }
        if result.method == "morris":
            payload["morris"] = {
                "trajectories": result.trajectories,
                "levels": result.levels,
                "random_seed": result.random_seed,
                "mu": result.morris_mu.tolist(),
                "mu_star": result.morris_mu_star.tolist(),
                "sigma": result.morris_sigma.tolist(),
                "mu_by_point": result.raw_sensitivity.tolist(),
                "mu_star_by_point": result.normalized_sensitivity.tolist(),
                "elementary_effects": result.elementary_effects.tolist(),
            }
        else:
            payload["local"] = {
                "perturbation_percent": result.perturbation_percent,
                "raw_sensitivity": result.raw_sensitivity.tolist(),
                "normalized_sensitivity": result.normalized_sensitivity.tolist(),
                "correlation": result.correlation.tolist(),
            }
        json.dump(payload, output, ensure_ascii=False, indent=2)
        output.write("\n")

    _atomic_text_file(json_path, write_json)
    result.json_path = json_path
    return json_path
