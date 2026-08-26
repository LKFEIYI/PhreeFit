# Enabled CD-MUSIC Performance Optimizations in IPhreeqc 3.8.6

## Scope

The optimized IPhreeqc library retains the original PHREEQC thermodynamic model, equilibrium equations, convergence tolerances, and public API. The changes reduce the computational cost of solving CD-MUSIC systems, primarily by avoiding redundant Jacobian work inside the Newton iteration.

The production build enables three optimizations:

1. one-step reuse of a complete CD-MUSIC Jacobian;
2. selective activity-coefficient recomputation during numerical differentiation;
3. local analytic Jacobian columns for the three CD-MUSIC surface-potential unknowns.

The implementation is located primarily in:

- `src/phreeqcpp/model.cpp`
- `src/phreeqcpp/Phreeqc.h`

## 1. One-Step CD-MUSIC Jacobian Reuse

### Original calculation

PHREEQC solves the nonlinear equilibrium system

\[
F(x)=0
\]

with Newton-type iterations. At iteration \(k\), it solves

\[
J(x_k)\Delta x=-F(x_k)
\]

and updates the state using \(\Delta x\). For CD-MUSIC, the original implementation normally rebuilt the complete Jacobian at every Newton iteration.

A numerical Jacobian with \(n\) unknowns requires approximately one base residual evaluation and one perturbed residual evaluation per column. Each perturbed evaluation may recalculate molalities, mass-balance sums, surface charge, and residuals. Jacobian construction therefore accounts for a large fraction of CD-MUSIC runtime.

### Optimized calculation

The optimized solver uses a conservative Modified Newton schedule:

```text
Iteration 1: build a complete Jacobian
Iteration 2: reuse that Jacobian
Iteration 3: build a new complete Jacobian
Iteration 4: reuse that Jacobian
...
```

Each complete Jacobian may be reused for only one subsequent Newton step. It is then rebuilt. This exploits the fact that the Jacobian often changes more slowly than the residual near a solution, while limiting the convergence risk associated with a stale matrix.

The solver records:

- whether the stored Jacobian is valid;
- the unknown count associated with the matrix;
- the number of times the matrix has been reused;
- whether the current matrix dimensions still match the equation system.

### Eligibility conditions

Reuse is enabled only when all relevant conditions are satisfied:

- the active surface model is `CD_MUSIC`;
- the internal surface diffuse-layer mode is `NO_DL`;
- no gas phase is active;
- no solid-solution assemblage is active;
- the solver is not in the explicit numerical-derivative mode;
- the number of unknowns and augmented-matrix shape are unchanged;
- the solver is not removing unstable phases.

### Invalidation

The stored Jacobian is invalidated when the equation structure or nonlinear state may no longer be compatible with it. This includes failed inequality handling, invalid molalities, basis or active-set changes, incompatible matrix dimensions, and unsupported model configurations.

This design preserves the original full-Jacobian path whenever reuse cannot be justified.

## 2. Selective Activity-Coefficient Recomputation

### Original calculation

The numerical Jacobian approximates column \(j\) using a finite difference:

\[
J_{ij}\approx-
\frac{F_i(x+\delta e_j)-F_i(x)}{\delta}.
\]

The original loop recalculated activity coefficients for every perturbed column, even when the ionic-strength variable had not changed.

### Optimization principle

Within a single numerical-Jacobian construction, the activity coefficients depend on the current ionic strength `mu_x`. Perturbing an unrelated unknown does not directly change `mu_x`, so repeatedly calling `gammas(mu_x)` with the same input is redundant.

The optimized loop recalculates activity coefficients only when the perturbed column is the ionic-strength unknown `MU`:

```cpp
if (x[i]->type == MU)
{
    gammas(mu_x);
}
```

All required calculations for each column remain active:

```text
molalities
mass-balance sums
residual evaluation
```

After the finite-difference loop, the base activity coefficients, molalities, mass-balance sums, and residuals are restored.

### Numerical meaning

This is an elimination of duplicate work, not a thermodynamic approximation. The `MU` column still includes the response of activity coefficients to a perturbed ionic strength, and the base activity coefficients are recomputed after the original ionic strength is restored.

## 3. Local Analytic CD-MUSIC Potential Columns

### Targeted unknowns

A CD-MUSIC surface charge group introduces three coupled potential or charge-balance unknowns:

```text
SURFACE_CB
SURFACE_CB1
SURFACE_CB2
```

The original solver obtained all three Jacobian columns by perturbing the corresponding unknowns and reevaluating the complete chemical residual system.

The optimized solver constructs only these three columns analytically. All other Jacobian columns continue to use the established PHREEQC numerical procedure.

### Existing reaction-summation information

PHREEQC already assembles reaction-summation derivatives through `jacobian_sums()`. The optimization uses this existing matrix as a seed and completes the CD-MUSIC potential columns with the required variable scaling, plane-charge accumulation, capacitance terms, and diffuse-layer derivative.

This avoids reimplementing the complete aqueous and surface speciation derivative system.

### Plane capacitance derivatives

For surface potentials \(\psi_0\), \(\psi_1\), and \(\psi_2\), the compact-layer charge relationships contain terms equivalent to

\[
\sigma_{C0}=C_0(\psi_0-\psi_1)
\]

and

\[
\sigma_{C1}=C_1(\psi_1-\psi_2).
\]

Their derivatives are direct:

\[
\frac{\partial\sigma_{C0}}{\partial\psi_0}=C_0,
\qquad
\frac{\partial\sigma_{C0}}{\partial\psi_1}=-C_0,
\]

\[
\frac{\partial\sigma_{C1}}{\partial\psi_1}=C_1,
\qquad
\frac{\partial\sigma_{C1}}{\partial\psi_2}=-C_1.
\]

The implementation applies the PHREEQC logarithmic-potential conversion

\[
\beta=\ln(10)\frac{RT}{F}
\]

and converts surface molar charge to charge per unit area using

\[
\text{scale}=\frac{F}{A_{\mathrm{specific}}m}.
\]

### Charge-balance column assembly

Using the plane-charge derivative terms supplied by the seed matrix, the three local residual derivatives have the form

\[
J_0=-\text{scale}\ln(10)q_0-
\frac{\partial\sigma_{C0}}{\partial x},
\]

\[
J_1=-\text{scale}\ln(10)(q_0+q_1)-
\frac{\partial\sigma_{C1}}{\partial x},
\]

and

\[
J_2=-\text{scale}\ln(10)(q_0+q_1+q_2)-
\frac{\partial\sigma_d}{\partial x}.
\]

The signs and scaling follow the internal PHREEQC convention in which the stored matrix is the negative residual derivative.

### Diffuse-layer derivative

For the third plane, the implementation evaluates the diffuse-layer derivative from the aqueous species distribution. With

\[
u=\ln(10)\log a_{\psi_2},
\]

it forms an ionic contribution

\[
S(u)=\sum_i m_i\left(e^{z_i u}-1\right)
\]

and its derivative

\[
S'(u)=\sum_i m_i z_i e^{z_i u}.
\]

The implementation also includes PHREEQC's charge-balancing counter-ion contribution. These quantities provide the derivative of the diffuse charge term containing \(\sqrt{|S(u)|}\).

### Smooth zero-potential limit

Direct evaluation near \(u=0\) can produce an unstable near-zero ratio. For small potential magnitude, the implementation uses the smooth limiting expression based on the second charge moment

\[
\sum_i m_i z_i^2.
\]

This avoids division by a very small value and prevents non-finite analytic derivatives near zero surface potential.

### Numerical fallback

The analytic columns are used only when the validated local structure is present. The builder verifies, among other conditions:

- a CD-MUSIC surface with the supported internal mode;
- absence of gas and solid-solution systems;
- absence of a pure-phase unknown in the local analytic path;
- the expected consecutive three-column surface-potential layout;
- valid matrix and unknown-vector sizes;
- valid surface, charge, master-species, and species pointers;
- positive surface mass and specific area;
- finite capacitance and diffuse-layer derivatives.

If any validation fails, the affected calculation uses the original numerical Jacobian path.

## Combined Execution Flow

The enabled optimizations combine as follows:

```text
Full-Jacobian Newton iteration
  1. Assemble the existing reaction-summation information.
  2. Build the three CD-MUSIC potential columns analytically when supported.
  3. Build the remaining columns by numerical differentiation.
  4. Recompute activity coefficients only for an ionic-strength perturbation.
  5. Solve the Newton linear system.

Next Newton iteration
  1. Reuse the validated complete Jacobian once.
  2. Solve the Newton linear system without rebuilding the Jacobian.

Following iteration
  1. Rebuild a new complete Jacobian and repeat the cycle.
```

The three changes reduce different components of the same cost:

- Jacobian reuse reduces how often a complete Jacobian is built.
- Selective `gammas()` evaluation reduces work inside each numerical build.
- Local analytic columns reduce the number of full residual perturbations required by each build.

## Validation Results

The enabled changes were compared with the corresponding IPhreeqc 3.8.6 baseline using identical candidate parameter vectors.

### One-step Jacobian reuse

- PO4 CD-MUSIC: 50 candidates, zero failures on both builds.
- Maximum absolute phosphorus concentration difference: `8.70e-11 mol/kgw`.
- Maximum absolute pH difference: `9.21e-6`.
- Median runtime reduction: approximately `30.96%`.
- Bacteria CD-MUSIC: 100 candidates, zero failures on both builds.
- Maximum absolute pH difference: `9.43e-7`.
- Median runtime reduction: approximately `39.21%`.

### Local analytic potential columns

- PO4 CD-MUSIC: 50 candidates and zero failures.
- Maximum absolute objective-function difference: `0.0`.
- Median objective-call runtime reduction over the preceding optimized build: approximately `1.21%`.
- Bacteria CD-MUSIC: 100 full-bound candidates and zero failures.
- Maximum absolute pH difference: `9.56e-7`.
- Median persistent-run reduction over the preceding optimized build: approximately `8.83%`.

### Full PhreeFit optimization path

For ten complete PO4 differential-evolution plus Nelder-Mead optimizations using four worker processes:

- IPhreeqc 3.7.3 wall time: `212.71 s`;
- optimized IPhreeqc 3.8.6 wall time: `124.48 s`;
- wall-time reduction: `41.48%`;
- maximum final-objective difference: approximately `5.00e-10`.

## Memory and State Safety

The optimization adds no manually managed dynamic allocation and no shared mutable global Jacobian buffer. Temporary matrices and vectors use `std::vector`, and reuse state belongs to the individual PHREEQC solver invocation.

The implementation checks matrix-size arithmetic, unknown counts, augmented-matrix dimensions, and relevant pointers before using optimized paths. Unsupported or inconsistent states deliberately return to the original numerical implementation.

Validation included native IPhreeqc tests, AddressSanitizer and UndefinedBehaviorSanitizer runs, separate leak checking on macOS, and static analysis. No memory-safety failure was reported for the tested CCM, CD-MUSIC, PO4, fresh-instance, persistent-instance, or delete-all paths.
