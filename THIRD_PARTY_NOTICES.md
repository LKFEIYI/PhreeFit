# Third-party notices

The MIT License in the repository root applies only to code written for
PhreeFit by the project copyright holder. It does not replace or supersede
the licenses of third-party components included in the source tree or in
the packaged application.

## IPhreeqc / PHREEQC

PhreeFit includes a modified copy of IPhreeqc 3.8.6-17100 under:

`iphreeqc/iphreeqc-3.8.6-17100`

The original USGS user-rights notice is preserved at:

`iphreeqc/iphreeqc-3.8.6-17100/doc/NOTICE`

The modified IPhreeqc source is not relicensed under the MIT License. When
redistributing it, retain the original notice and clearly identify the
modifications, their author, and the modification date, as required by that
notice. Do not imply endorsement by the U.S. Geological Survey.

## Python and runtime dependencies

The packaged application may include components whose licenses must remain
available to recipients, including (depending on the build):

- PySide6 / Qt — LGPL and/or Qt commercial licensing terms;
- NumPy — BSD-style license and notices for bundled components;
- SciPy — BSD-style license and notices for bundled components;
- pyqtgraph — MIT License;
- phreeqpy — BSD 3-Clause License;
- Cython — Apache License 2.0;
- PyInstaller — GPLv2-or-later with its bootloader exception for bundled
  applications.

Before publishing an installer, generate or review a complete dependency
license inventory for the exact environment used to build that installer and
ship the corresponding license texts with the application.
