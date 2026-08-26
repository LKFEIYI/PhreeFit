# PhreeFit 1.0.0 Release Notes

PhreeFit 1.0.0 is the first stable release of the desktop application for
PHREEQC/IPhreeqc-based surface complexation model fitting, result analysis,
and parameter sensitivity analysis. This release supports the principal
Titration and Advanced workflows on macOS and Windows.

## Features

- Added Titration and Advanced fitting workflows with support for NEM, CCM,
  and CD-MUSIC surface complexation models.
- Integrated an optimized IPhreeqc 3.8.6 calculation engine:
  - Persistent CCM calculations improved by 9.1% in the benchmark.
  - Persistent CD-MUSIC calculations improved by 14.8%.
  - CD-MUSIC Modified Newton reuse improved PO4 calculations by 31.0% and
    bacteria calculations by 39.2%.
  - Local analytic CD-MUSIC potential derivatives added a further 8.83%
    improvement for the bacteria workload and 1.21% for PO4 objective calls.
  - A complete PO4 optimization was 41.48% faster than IPhreeqc 3.7.3, with a
    maximum paired final-objective difference of `5.00e-10`.
  - The benchmark produced exact selected-output matches for the tested CCM
    and CD-MUSIC candidate sets.
- Added parameter sensitivity analysis:
  - Morris screening is the default method.
  - Local finite-difference analysis is also available.
  - Morris results include mu, mu-star, sigma, and response heatmaps.
  - Local results include parameter importance, signed sensitivity heatmaps,
    and sensitivity-profile correlation.
  - Results are stored exclusively as JSON files and can be loaded later.
  - Users can return from a result view to the sensitivity settings dialog.
  - Help dialogs provide concise guidance for interpreting Morris and local
    sensitivity results.
- Added numerical parameter uncertainty estimation after optimization:
  - A finite-difference Jacobian is used to estimate one-standard-deviation
    parameter uncertainty.
  - Optimized parameters are reported as `value(uncertainty)` in both the
    result view and log file.
  - Unavailable or numerically unreliable estimates are reported as `n/a`.
- Added JSON-based settings management:
  - Database, data, output paths, text fields, checkboxes, and model settings
    can be saved and restored.
  - Titration and Advanced settings are stored separately.
  - Existing settings files remain compatible.
  - Missing shared paths are allowed and reported to the user instead of
    preventing the remaining settings from loading.
- Expanded History tools:
  - Optimization records are read from the current Output path.
  - Records display task, time, R2, adjusted R2, BIC, RMSE, and V(Y).
  - Comparison plots use adjusted R2 on the left axis and BIC on the right.
  - Hovering over a comparison point displays its task name and timestamp.
  - Selected log records can be viewed in full.
  - Selected history entries and their corresponding result records can be
    cleared.
  - The current Output path can be opened in the native system file browser.
- Added optional plotting of major surface species:
  - Surface species are plotted on a secondary right axis.
  - Species belonging to the same surface use the same marker symbol.
  - Individual species use distinct colors and dashed lines.
  - Titration plots retain Volume on the x-axis and pH on the primary y-axis.
  - Surface-species curves are hidden by default and can be enabled as needed.
- Moved application configuration to a user-writable location on both macOS
  and Windows.
- Added application version metadata and release-aware packaging. The current
  version is `1.0.0`.

## Fixes

- Fixed incorrect process-count handling during optimization.
- Replaced unsafe forced thread termination with cooperative cancellation.
- Added reliable `try/finally` cleanup for workers, files, and IPhreeqc
  instances, reducing the risk of resource leaks and `Too many open files`
  errors.
- Fixed an intermittent crash when repeatedly switching between the
  Titration, Plot, and Advanced pages.
- Fixed result plots not appearing in packaged macOS application bundles.
- Fixed incorrect bounds-label rendering in the macOS Titration interface.
- Fixed optimization starting after the task-name dialog was closed or
  cancelled.
- Changed Advanced Titration mode to reload the current data file
  automatically when selected.
- Fixed a constructor initialization spelling error.
- Fixed the initial C2 value used by CD-MUSIC models.
- Fixed missing and incorrectly ordered fitted parameter bounds.
- Fixed inconsistent handling of scalar and ranged surface parameters in the
  surface summary.
- Added missing initial values for fitted sites, reaction constants, charge
  parameters, and capacitance parameters to the surface summary.
- Added a prominent warning when an initial value falls outside its bounds.
- Clarified which surface capacitance parameter is fitted in CCM models.
- Fixed missing visual selection feedback in the History table.
- Fixed settings loading when referenced database or data paths do not exist
  on another computer.
- Fixed the Results panel overlapping the raw-data display area.

### IPhreeqc safety hardening

- Added validation for matrix dimensions, integer ranges, pointers, finite
  values, and Jacobian layouts in optimized calculation paths.
- Added safe fallback to the original numerical implementation whenever an
  optimized configuration is unsupported or fails validation.
- Validated the native library with release tests, static analysis,
  sanitizer-assisted tests, memory-leak checks, and representative PO4, CCM,
  and CD-MUSIC workloads on macOS arm64.

## Refactor

- Reorganized the application into separate interface, signal/controller,
  input/output, plotting, sensitivity-analysis, and background-worker layers.
- Removed the runtime pandas dependency and replaced dataframe-based paths
  with NumPy and lightweight table models.
- Rebuilt the Titration and Advanced pages with Qt layouts, splitters, scroll
  areas, and responsive size policies for better use on different screen
  sizes.
- Reorganized the parameter panels around Output, Set Parameters,
  Species/Reactions, Optimization, and a larger Optimize action.
- Refactored IPhreeqc lifecycle management so each process and worker thread
  owns an independent cached instance, databases trigger safe reinitialization,
  and completed or failed calculations release native resources reliably.
- Improved macOS and Windows packaging:
  - The platform-specific optimized IPhreeqc library is selected explicitly.
  - Packaged applications no longer rely on phreeqpy's default IPhreeqc 3.7.3
    library filename.
  - Native-library existence, architecture, and required exports are checked
    during packaging.
  - Cython-compiled calculation modules and standalone application bundles are
    supported.
