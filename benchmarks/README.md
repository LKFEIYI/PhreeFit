# IPhreeqc 3.8.6 optimization benchmark

The library currently shipped in `packaging/lib` combines three enabled C++
optimizations: one-step CD-MUSIC Modified Newton reuse, activity-coefficient
recalculation only for the numerical `MU` column, and local analytic
`SURFACE_CB/CB1/CB2` columns where the supported equation layout permits it.
See `packaging/lib/README.md` for the exact activation/fallback conditions,
current binary hash, safety hardening, and sanitizer results.

The benchmark uses 50 candidate parameter vectors, 20 titration points, three
surface sites, and the CCM and CD-MUSIC models in `test/bac`. Times are per
candidate. Release libraries were compiled with `-O3 -DNDEBUG
-mcpu=apple-m1`.

| Workload | 3.8.6 baseline median | Optimized median | Change |
| --- | ---: | ---: | ---: |
| CCM, fresh instance total | 2.689 ms | 2.710 ms | -0.8% (noise) |
| CCM, persistent run + extract | 2.588 ms | 2.352 ms | +9.1% |
| CD-MUSIC, fresh instance total | 30.538 ms | 26.817 ms | +12.2% |
| CD-MUSIC, persistent run + extract | 29.967 ms | 25.544 ms | +14.8% |

The 3.8.6 C++ change produced an exact selected-output match against the
baseline for all 50 CCM and 50 CD-MUSIC candidates (`max_abs_delta == 0`).
Persistent instances also returned exactly 20 result rows on every run. The
largest pH difference caused by using the previous solution as the next
initial state was `1.77e-8` for CCM and `1.35e-7` for CD-MUSIC at the default
`1e-8` convergence tolerance.

PhreeFit optimization calls use `1e-7`, while the final reported result starts
from a new instance and uses `1e-8`. After 11 cached optimization calls, that
final result matched a separate fresh-instance calculation exactly for both
models.

## CD-MUSIC modified Newton test

The second optimization reuses each complete CD-MUSIC numerical Jacobian for
one Newton step and rebuilds it on the next step. Reuse is cancelled after an
inequality-solver failure, basis change, mass-water equation change, or an
unstable-phase transition.

| Workload | Candidates | Baseline median | Modified Newton median | Change |
| --- | ---: | ---: | ---: | ---: |
| PO4, 36 points and full parameter bounds | 50 | 95.85 ms | 66.17 ms | +31.0% |
| Bacteria, 20 points and full parameter bounds | 100 | 52.44 ms | 31.87 ms | +39.2% |

Both tests had zero calculation failures and no output-shape mismatches. The
largest PO4 concentration difference was `8.70e-11 mol/kgw`; its largest pH
difference was `9.21e-6`. The bacteria test's largest pH difference was
`9.43e-7`. CCM is not subject to Jacobian reuse and matched exactly.

A residual-threshold variant was rejected: switching unpredictably between
reuse and rebuilding made the PO4 median 7.7% slower than the baseline. The
strict alternating implementation above was used instead.

Raw results are in:

- `results/iphreeqc_3.8.6_baseline.json`
- `results/iphreeqc_3.8.6_optimized.json`
- `results/iphreeqc_3.8.6_modified_newton_summary.json`

## Experimental Jacobian methods

Three additional CD-MUSIC methods were implemented behind compile-time
switches and measured. They are disabled in the final build because none
improved the validated workload:

| Method | Result |
| --- | --- |
| Safeguarded Broyden rank-one update | 11.89 to 25.14 ms; mean iterations 48.8 to 65.9 |
| Hybrid analytic/numerical Jacobian | Rejected after the warm-up case failed to converge |
| Sparse finite-difference coloring | 13 columns formed 8 groups, but 22.55 to 23.20 ms and mean iterations 53.5 to 62.7 |

The final disabled-feature build was also tested with 50 PO4 candidates and
36 data points. All objective values matched the current packaging library
exactly; median times were 31.23 and 31.20 ms respectively (measurement
noise). Detailed results are in
`results/iphreeqc_3.8.6_experimental_jacobian_summary.json`.

Run the benchmark with:

```bash
python benchmarks/benchmark_iphreeqc.py \
  --dll /path/to/libiphreeqc-3.8.6.dylib \
  --label 3.8.6-optimized --repeats 50 --points 20
```

The PO4 objective-only regression (it does not run differential evolution) is:

```bash
python benchmarks/benchmark_po4_candidates.py \
  --dll /path/to/libiphreeqc-3.8.6.dylib --candidates 50
```

## Local analytic CD-MUSIC Jacobian

The three CD-MUSIC potential columns (`SURFACE_CB`, `SURFACE_CB1`, and
`SURFACE_CB2`) now use analytic derivatives assembled from the existing
reaction summation matrix, the capacitance equations, and an analytic
diffuse-layer derivative. The zero-potential diffuse term uses its smooth
symbolic limit to avoid cancellation. Unsupported configurations and
non-finite derivatives retain the original numerical columns.

SymPy 1.14.0 from the `phreefit` conda environment was used only for
development and verification; the compiled library has no SymPy or Python
dependency. The local symbolic expression matched central differences to
`2.84e-12` maximum absolute error.

| Workload | Current packaging median | Local analytic median | Change |
| --- | ---: | ---: | ---: |
| Bacteria, 50 candidates × 20 points | 11.58 ms | 10.56 ms | +8.83% |
| PO4 objective, 50 candidates × 36 points | 32.00 ms | 31.61 ms | +1.21% |

Three sequential timing repetitions were used. A 100-candidate bacteria
full-bounds regression and the 50-candidate PO4 regression had zero failures;
all final PO4 objective values matched the current packaging library exactly.
See `results/iphreeqc_3.8.6_local_analytic_summary.json` and run the symbolic
check with `phreefit/bin/python benchmarks/derive_cdmusic_jacobian.py`.

## Full PO4 optimization against 3.7.3

Ten paired complete optimizations used `main_cal.advanced_fun_auto`, DE with
`popsize=8`, and Nelder-Mead polish. Seeds 42 through 420 and four workers were
identical for both libraries.

| Library | Successful runs | Wall time | Mean run time | Median run time |
| --- | ---: | ---: | ---: | ---: |
| Optimized 3.8.6 | 10/10 | 124.48 s | 41.68 s | 41.49 s |
| IPhreeqc 3.7.3 | 10/10 | 212.71 s | 73.38 s | 72.94 s |

The optimized library reduced total wall time by 41.48% and mean per-run time
by 43.21%. The maximum paired final-objective difference was `5.00e-10`.
Results are in `test/po4/po4_full_optimization_new_3.8.6_10runs.json` and
`test/po4/po4_full_optimization_3.7.3_10runs.json`.

## Memory-safety verification

The final source was diffed recursively against `iphreeqc/raw_source`; only
`model.cpp` and `Phreeqc.h` differ. Release and ASan/UBSan native tests passed
2/2. Instrumented PO4, CCM, and CD-MUSIC workloads completed without sanitizer
reports. Clang static analysis found no pointer, bounds, or lifetime issue in
the current changes; two possible null dereferences reported in `raw_source`
were explicitly guarded in the optimized source. Detailed scope and limitations
are recorded in `packaging/lib/README.md`.
