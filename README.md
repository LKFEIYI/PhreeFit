# PhreeFit

PhreeFit is a desktop application for fitting and analyzing surface complexation models using PHREEQC / IPhreeqc. It is designed for parameter optimization, result visualization, and sensitivity analysis of titration and adsorption experiment data. PhreeFit provides a graphical user interface and does not require users to install Python or compile the source code.

Current version: **1.0.0**

## Key Features

- Titration and Advanced analysis workflows.
- Support for NEM, CCM, and CD-MUSIC surface complexation models.
- Differential Evolution, Dual Annealing, and Nelder–Mead optimization algorithms.
- Configurable initial values and fitting bounds for surface sites, reaction constants, charge parameters, and capacitance parameters.
- Visualization of fitted curves, experimental data, and major surface species, with plot export to PNG or SVG.
- Parameter sensitivity analysis using Morris screening or local finite differences. Results can be saved as JSON files and loaded again later.
- Numerical parameter uncertainty estimates after optimization, together with R², adjusted R², BIC, RMSE, and other fitting statistics.
- Saving and loading of database paths, data paths, model parameters, and other analysis settings.
- Viewing, comparing, and clearing previous optimization results.

## Installation

The PhreeFit installation packages include the components required to run the application. You do not need to configure a Python environment or compile the source code.

### macOS

Supported platform: Macs with Apple silicon, including M1, M2, M3, and M4 processors.

1. Download `PhreeFit-1.0.0-arm64.dmg`.
2. Double-click the DMG file to open it.
3. Drag `PhreeFit` into the `Applications` folder.
4. Open PhreeFit from the Applications folder.

If macOS reports that it cannot verify the developer when the application is opened for the first time, confirm that the package came from a trusted PhreeFit release, then go to **System Settings → Privacy & Security** and select **Open Anyway**.

> The current DMG is built for arm64 and does not support Intel-based Macs.

### Windows

Supported platform: 64-bit Windows 10 or Windows 11.

1. Download the Windows installer whose filename ends in `setup.exe`.
2. Double-click the installer and follow the setup wizard.
3. Start PhreeFit from the Start menu or desktop shortcut.
4. To uninstall PhreeFit, open **Settings → Apps → Installed apps**, locate PhreeFit, and select **Uninstall**.

If Microsoft Defender SmartScreen displays a warning during installation, first confirm that the installer came from a trusted PhreeFit release, then follow the Windows prompts to continue.

## Basic Usage

1. Start PhreeFit and select a PHREEQC database file.
2. Load the experimental data from a CSV file, then configure the data columns, experimental conditions, and output directory.
3. Select the NEM, CCM, or CD-MUSIC model and enter the surface, species, and reaction parameters.
4. Set the initial values and bounds of the parameters to be fitted, then select an optimization algorithm.
5. Run the optimization and review the fitted parameters, statistics, and plots.
6. Save the settings, export plots, compare previous results, or run a sensitivity analysis as needed.

> Model-fitting results depend on the selected database, experimental data, initial values, and parameter bounds. Before using the results in production or research, validate the input settings and output against a known reference case.

## License

Code written by the PhreeFit project copyright holder is released under the [MIT License](LICENSE). You may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, provided that the copyright and license notices are retained in all copies or substantial portions of the software. The software is provided “as is,” without warranty of any kind.

PhreeFit also includes third-party components such as PHREEQC / IPhreeqc, Qt / PySide6, NumPy, and SciPy. These components remain subject to their respective licenses and copyright notices. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for details. The project's MIT License does not replace or override the license terms of any third-party component.

Copyright (c) 2026 lyt
