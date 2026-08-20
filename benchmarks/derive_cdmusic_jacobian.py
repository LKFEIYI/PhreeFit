"""Derive and verify the local CD-MUSIC potential Jacobian with SymPy.

Run this development-only script with the ``phreefit`` conda environment.
The generated formulas target the log10 potential activities used by
``numerical_jacobian``. IPhreeqc stores the negative residual derivative in
``my_array``; this script prints the residual derivative before that sign is
applied.
"""

from __future__ import annotations

import math

import numpy as np
import sympy as sp


def symbolic_jacobian():
    l0, l1, l2 = sp.symbols("l0 l1 l2", real=True)
    beta, c1, c2, scale = sp.symbols("beta C1 C2 scale", positive=True)
    kappa, aqueous_charge = sp.symbols("kappa Qabs", positive=True)
    potential_sign, charge_sign = sp.symbols("potential_sign charge_sign", real=True)

    # Two generic surface species are sufficient for SymPy to establish the
    # sum pattern d(q_p)/d(l_q) = ln(10) sum(m_s dz_sp dz_sq).
    reference_molality = sp.symbols("m0:2", positive=True)
    dz = [[sp.symbols(f"dz{s}{plane}", real=True) for plane in range(3)] for s in range(2)]
    log10 = sp.log(10)
    molality = [
        reference_molality[s]
        * sp.exp(log10 * sum(dz[s][plane] * (l0, l1, l2)[plane] for plane in range(3)))
        for s in range(2)
    ]
    plane_charge = [
        sum(molality[s] * dz[s][plane] for s in range(2))
        for plane in range(3)
    ]

    psi = [-beta * value for value in (l0, l1, l2)]
    residual0 = scale * plane_charge[0] - c1 * (psi[0] - psi[1])
    residual1 = scale * (plane_charge[0] + plane_charge[1]) - c2 * (psi[1] - psi[2])

    # The diffuse-layer derivative is represented separately. Its direct
    # l2 derivative is added after differentiating the three surface planes.
    diffuse = sp.Function("sigma_ddl")(l2)
    residual2 = scale * sum(plane_charge) + diffuse
    jacobian = sp.Matrix([residual0, residual1, residual2]).jacobian([l0, l1, l2])

    u = log10 * l2
    aqueous_m = sp.symbols("aq_m0:2", positive=True)
    aqueous_z = sp.symbols("aq_z0:2", real=True)
    diffuse_sum = sum(
        aqueous_m[i] * (sp.exp(aqueous_z[i] * u) - 1) for i in range(2)
    ) + aqueous_charge * (sp.exp(-charge_sign * u) - 1)
    diffuse_expression = potential_sign * sp.Rational(1, 2) * kappa * sp.sqrt(diffuse_sum)
    diffuse_derivative = sp.diff(diffuse_expression, l2)
    jacobian[2, 2] = jacobian[2, 2].subs(sp.diff(diffuse, l2), diffuse_derivative)
    return (l0, l1, l2), jacobian


def zero_potential_limit():
    """Return d(sigma_ddl)/d(l2) at l2=0 from the symmetric limit."""
    log10, kappa, second_moment = sp.symbols(
        "log10 kappa second_moment", positive=True
    )
    # S(u) = second_moment*u**2/2 + O(u**3), while
    # sign(u)*sqrt(S(u)) has the smooth local form u*sqrt(A/2).
    return sp.simplify(
        sp.Rational(1, 2) * kappa * log10 * sp.sqrt(second_moment / 2)
    )


def numerical_verification() -> float:
    rng = np.random.default_rng(386)
    ln10 = math.log(10.0)
    beta, c1, c2, scale, kappa = 0.05916, 0.74, 0.93, 2.7, 0.1174
    logs = np.array([-0.3, 0.1, 0.25])
    base_m = rng.uniform(1e-7, 3e-4, 5)
    dz = rng.uniform(-2.0, 2.0, (5, 3))
    aq_m = np.array([0.08, 0.02, 0.001])
    aq_z = np.array([1.0, -1.0, 2.0])

    def residual(values: np.ndarray) -> np.ndarray:
        species_m = base_m * np.exp(ln10 * (dz @ values))
        charge = species_m @ dz
        psi = -beta * values
        u = ln10 * values[2]
        q = float(aq_m @ aq_z)
        q_sign = 1.0 if q >= 0 else -1.0
        diffuse_sum = float(np.sum(aq_m * (np.exp(aq_z * u) - 1.0)))
        diffuse_sum += abs(q) * (math.exp(-q_sign * u) - 1.0)
        diffuse = math.copysign(0.5 * kappa * math.sqrt(abs(diffuse_sum)), u)
        return np.array(
            [
                scale * charge[0] - c1 * (psi[0] - psi[1]),
                scale * (charge[0] + charge[1]) - c2 * (psi[1] - psi[2]),
                scale * float(np.sum(charge)) + diffuse,
            ]
        )

    species_m = base_m * np.exp(ln10 * (dz @ logs))
    charge_derivative = ln10 * np.einsum("s,sp,sq->pq", species_m, dz, dz)
    analytic = np.empty((3, 3))
    analytic[0] = scale * charge_derivative[0]
    analytic[0, 0] += c1 * beta
    analytic[0, 1] -= c1 * beta
    analytic[1] = scale * (charge_derivative[0] + charge_derivative[1])
    analytic[1, 1] += c2 * beta
    analytic[1, 2] -= c2 * beta
    analytic[2] = scale * np.sum(charge_derivative, axis=0)

    u = ln10 * logs[2]
    q = float(aq_m @ aq_z)
    q_sign = 1.0 if q >= 0 else -1.0
    diffuse_sum = float(np.sum(aq_m * (np.exp(aq_z * u) - 1.0)))
    diffuse_sum += abs(q) * (math.exp(-q_sign * u) - 1.0)
    dsum_dl2 = ln10 * float(np.sum(aq_m * aq_z * np.exp(aq_z * u)))
    dsum_dl2 -= ln10 * abs(q) * q_sign * math.exp(-q_sign * u)
    analytic[2, 2] += math.copysign(1.0, u) * kappa * dsum_dl2 / (
        4.0 * math.sqrt(abs(diffuse_sum))
    )

    step = 1e-6
    finite_difference = np.column_stack(
        [
            (residual(logs + np.eye(3)[column] * step)
             - residual(logs - np.eye(3)[column] * step))
            / (2.0 * step)
            for column in range(3)
        ]
    )
    error = float(np.max(np.abs(analytic - finite_difference)))
    print("analytic 3x3:\n", analytic)
    print("central difference 3x3:\n", finite_difference)
    print("max_abs_error:", error)
    return error


if __name__ == "__main__":
    variables, jacobian = symbolic_jacobian()
    print("variables:", variables)
    print("symbolic residual Jacobian shape:", jacobian.shape)
    print("zero-potential diffuse derivative:", sp.ccode(zero_potential_limit()))
    for row in range(3):
        for column in range(3):
            print(f"dR{row}/dl{column} = {sp.ccode(sp.simplify(jacobian[row, column]))}")
    if numerical_verification() > 1e-8:
        raise SystemExit("symbolic/local numerical verification failed")
