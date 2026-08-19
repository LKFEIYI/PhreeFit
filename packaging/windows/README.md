# PhreeFit Windows packaging

The Windows build uses `src_new` as its only application source. It builds the
calculation module as a Cython `.pyd`, bundles the Windows IPhreeqc DLL, creates
a portable ZIP, and optionally creates a standard installer with Inno Setup 6.

## Requirements

- 64-bit Windows 10 or 11
- 64-bit CPython (Python 3.10 is recommended to match the existing builds)
- Microsoft C++ Build Tools with the C++ compiler and Windows SDK
- Inno Setup 6 if a `Setup.exe` installer is required

Install the Python build dependencies in a clean virtual environment:

```powershell
py -3.10 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\packaging\windows\requirements-build.txt
```

All Python packages, the compiled `.pyd`, and IPhreeqc DLL must be x64. Do not
mix 32-bit, ARM64, and x64 components in the same build environment.

## Build

From the project root:

```powershell
.\packaging\windows\build_windows.ps1 -Version 1.0.0 -Python python
```

Outputs:

- `dist\windows\PhreeFit\PhreeFit.exe` and its runtime files
- `dist\windows\PhreeFit-1.0.0-win-x64.zip`
- `dist\windows\PhreeFit-1.0.0-win-x64-setup.exe` when Inno Setup is installed

To build only the application and portable ZIP:

```powershell
.\packaging\windows\build_windows.ps1 -Version 1.0.0 -SkipInstaller
```

If Inno Setup is installed in a custom location:

```powershell
.\packaging\windows\build_windows.ps1 -Version 1.0.0 `
  -InnoSetupCompiler "D:\Tools\Inno Setup 6\ISCC.exe"
```

The script copies `src_new` to `build\windows\stage` before compiling, so
generated C and `.pyd` files do not modify the source tree.

## Manual test checklist

1. Run `dist\windows\PhreeFit\PhreeFit.exe` before creating a release.
2. Load a PHREEQC database and representative CSV data.
3. Run both titration and advanced calculations.
4. Save and reload settings and optimization history.
5. Install with `Setup.exe`, launch from the Start menu, then uninstall it.
6. Repeat on a clean Windows x64 machine without Python installed.

For public distribution, sign `PhreeFit.exe` and the final installer with an
Authenticode code-signing certificate. This configuration does not sign files
automatically because certificate providers and signing services differ.
