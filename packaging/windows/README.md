# PhreeFit Windows packaging

## Standalone optimized IPhreeqc DLL source package

`iphreeqc-3.8.6-17100-optimized-win-x64-source.zip` contains the complete
optimized source and an offline one-click DLL build script. After extraction,
double-click `build_iphreeqc_dll.cmd`; the validated Release x64 DLL is written
to `output\win-x64`. The script source and detailed requirements are maintained
in `iphreeqc_dll_builder`.

The Windows build uses `src_new` as its only application source. It builds the
calculation module as a Cython `.pyd`, bundles the Windows IPhreeqc DLL, creates
a portable ZIP, and optionally creates a standard installer with Inno Setup 6.
The installer script uses Inno Setup's built-in English messages and does not
depend on optional language files installed separately.

## Requirements

- 64-bit Windows 10 or 11
- 64-bit CPython (Python 3.10 is recommended to match the existing builds)
- Microsoft C++ Build Tools with the C++ compiler and Windows SDK
- CMake 3.20 or newer when an optimized prebuilt DLL is not supplied
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

The release version is read from `src_new\version.py`; update that file before
building a new release. The optional `-Version` argument must match it.

```powershell
.\packaging\windows\build_windows.ps1 -Python python
```

The build uses the optimized IPhreeqc 3.8.6 library in this order:

1. `-IPhreeqcDll` when explicitly supplied;
2. `packaging\lib\IPhreeqc-3.8.6.dll` when present;
3. otherwise it builds a Release x64 DLL from
   `iphreeqc\iphreeqc-3.8.6-17100` with CMake.

The selected DLL is bundled as `iphreeqc\IPhreeqc-3.8.6.dll`. A PyInstaller
runtime hook sets `PHREEFIT_IPHREEQC_LIBRARY`, so `main_cal` does not fall back
to phreeqpy's IPhreeqc 3.7.3 DLL.

When the DLL is built from the repository source it includes the same one-step
CD-MUSIC Modified Newton reuse, reduced activity-coefficient recomputation,
local analytic potential columns, and memory-safety guards documented in
`packaging/lib/README.md`. A prebuilt DLL supplied with `-IPhreeqcDll` must be
built from the same source revision to provide those optimizations.

To use an already compiled optimized DLL:

```powershell
.\packaging\windows\build_windows.ps1 -Python python `
  -IPhreeqcDll C:\build\IPhreeqc-3.8.6.dll
```

Outputs:

- `dist\windows\PhreeFit\PhreeFit.exe` and its runtime files
- `dist\windows\PhreeFit-1.0.0-win-x64.zip`
- `dist\windows\PhreeFit-1.0.0-win-x64-setup.exe` when Inno Setup is installed

To build only the application and portable ZIP:

```powershell
.\packaging\windows\build_windows.ps1 -SkipInstaller
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
