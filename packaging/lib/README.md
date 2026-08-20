# PhreeFit IPhreeqc library

This directory contains the native IPhreeqc library selected by PhreeFit at
runtime. The current macOS arm64 release is:

- file: `libiphreeqc-3.8.6.dylib`
- source: `iphreeqc/iphreeqc-3.8.6-17100`
- pristine comparison source: `iphreeqc/raw_source`
- SHA-256: `1407939290aeff1c740cd2dc9b3127f866377cdec6449aa7ce93e819a6d3c98d`

The source comparison differs only in `src/phreeqcpp/model.cpp` and
`src/phreeqcpp/Phreeqc.h`.

## Enabled C++ optimizations

1. **CD-MUSIC Modified Newton.** A complete Jacobian is reused for one Newton
   step and rebuilt on the next. Reuse requires CD-MUSIC, `NO_DL`, no gas
   phase, no solid solution, a stable unknown count and matrix shape, and
   `numerical_deriv == FALSE`. Pure-phase unknowns remain supported for the
   PO4 `Fix_H+` workflow. Reuse is cancelled after an inequality failure,
   molality failure, basis change, mass-water equation change, or unsupported
   equation configuration.
2. **Reduced activity-coefficient work.** During a numerical Jacobian,
   `gammas(mu_x)` is recalculated for the perturbed `MU` column instead of
   redundantly recalculating it for every finite-difference column. The base
   activity coefficients are restored after the loop.
3. **Local analytic CD-MUSIC potential columns.** `SURFACE_CB`,
   `SURFACE_CB1`, and `SURFACE_CB2` use derivatives assembled from the existing
   reaction-summation matrix, capacitance equations, and analytic diffuse-layer
   derivative. The zero-potential term uses its smooth limit. This path requires
   CD-MUSIC, `NO_DL`, no gas phase, no solid solution, no pure-phase unknown,
   finite values, and a valid matrix/unknown layout. Otherwise all three
   columns fall back to the original numerical Jacobian.

CCM does not use Modified Newton or the CD-MUSIC analytic columns. The compiled
library has no SymPy dependency; SymPy 1.14.0 in the `phreefit` environment was
used only to derive and verify the local analytic expressions.

## Safety hardening

- The analytic builder checks matrix-size multiplication for overflow, validates
  `my_array`, `seed`, and `x` sizes, and checks surface, master, species, and
  charge pointers before dereferencing them.
- Jacobian reuse records the unknown count and validates the augmented matrix
  shape before every reuse.
- Two potential null dereferences inherited from upstream 3.8.6 around
  `Find_charge()` are guarded, and gas-phase backup uses the already validated
  local pointer.
- New temporary storage uses `std::vector`; the optimization adds no manual
  `new`, `delete`, `malloc`, `free`, or shared global mutable buffer.

Validation performed on macOS arm64:

- release native IPhreeqc tests: 2/2 passed;
- ASan + UBSan native tests: 2/2 passed with no sanitizer report;
- ASan + UBSan PO4: 10 candidates, zero failures or reports;
- ASan + UBSan CCM and CD-MUSIC: 10 runs per model across fresh, persistent,
  and delete-all paths, zero failures or reports;
- macOS `leaks` on the native C++ test: exit 0 with no leak record;
- clang static analyzer: no pointer, bounds, lifetime, or undefined-behavior
  finding in the current changes. Four remaining dead-store warnings are also
  present in `raw_source`; two upstream possible-null findings were removed by
  the hardening above.

LeakSanitizer's `detect_leaks=1` is not supported by the current macOS ASan
runtime, so leak checking was performed separately with `/usr/bin/leaks`.
These checks provide strong coverage for the tested paths, but are not a formal
proof for every possible PHREEQC input combination. Unsupported analytic and
reuse configurations deliberately take the original numerical path.

## Measured behavior

- PO4, 50 objective calls after safety hardening: 31.49 ms median, zero
  failures, and all objective values exactly equal to the pre-hardening local
  analytic build.
- PO4, ten complete DE + Nelder-Mead optimizations with four workers: the new
  3.8.6 build used 124.48 s wall time versus 212.71 s for IPhreeqc 3.7.3,
  reducing wall time by 41.48%. The maximum final-objective difference was
  `5.00e-10`.
- Earlier isolated local-analytic measurements improved the bacteria workload
  by 8.83% and the PO4 objective workload by 1.21% on top of the preceding
  3.8.6 optimizations.

Experimental Broyden rank-one updates, full hybrid analytic Jacobian, and
finite-difference coloring remain compile-time disabled (`0`) because they did
not improve the validated workloads. They are not active in this binary.
