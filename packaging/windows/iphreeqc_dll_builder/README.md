# Optimized IPhreeqc 3.8.6 Windows DLL source package

This package contains the optimized IPhreeqc 3.8.6-17100 source used by
PhreeFit and an offline one-click Windows x64 build script.

## Requirements

- 64-bit Windows 10 or 11;
- Visual Studio 2022 Build Tools or Visual Studio 2022 with **Desktop
  development with C++** and a Windows SDK;
- CMake 3.20 or newer, with `cmake.exe` available on `PATH`.

No Python, Fortran compiler, Git, or network download is required.

## One-click build

1. Extract the complete ZIP to any writable path.
2. Double-click `build_iphreeqc_dll.cmd`.
3. Find the result in `output\win-x64`.

The command script uses Visual Studio Installer's `vswhere.exe` to locate the
latest Visual Studio installation containing the x64/x86 C++ build tools. It
then runs `VsDevCmd.bat` automatically, so `cl.exe`, `INCLUDE`, `LIB`, and the
Windows SDK do not need to be added to the user's permanent `PATH`. It can be
launched from Command Prompt, PowerShell, or Anaconda PowerShell.

To avoid the traditional CMake/MSVC object-path limit, the PowerShell script
mirrors the source to `%TEMP%\PhreeFit-IPhreeqc386` and builds there with the
`NMake Makefiles` generator. The final files are still copied back to
`output\win-x64` beside the script. A different short working directory may be
selected with `-WorkRoot C:\ipq386`.

The script produces:

- `IPhreeqc.dll`;
- `IPhreeqc-3.8.6.dll`, an identical versioned copy for PhreeFit;
- `IPhreeqc.lib`, when produced by MSVC;
- public C/C++ headers;
- `SHA256SUMS.txt`.

It builds Release x64 with MSVC optimization and interprocedural optimization
(LTO), then checks the PE architecture, loads the DLL, and verifies the
`CreateIPhreeqc`, `DestroyIPhreeqc`, `LoadDatabase`, and `RunString` exports.

To discard the previous build first, run:

```bat
build_iphreeqc_dll.cmd -Clean
```

Use `-Clean` after any failed CMake configuration so an incomplete compiler
cache is not reused.

If a specific MSVC/CMake combination cannot perform LTO, use:

```bat
build_iphreeqc_dll.cmd -Clean -DisableLto
```

If the configured `%TEMP%` path is unusually long, use:

```bat
build_iphreeqc_dll.cmd -Clean -WorkRoot C:\ipq386
```

## Enabled source optimizations

- one-step Modified Newton Jacobian reuse for the supported CD-MUSIC path;
- removal of redundant activity-coefficient recalculation from non-`MU`
  numerical Jacobian columns;
- local analytic `SURFACE_CB`, `SURFACE_CB1`, and `SURFACE_CB2` CD-MUSIC
  potential columns;
- matrix-size, pointer, finite-value, integer-overflow, and fallback safety
  checks.

Unsupported configurations automatically use the original numerical path.
Experimental Broyden, full hybrid analytic Jacobian, and coloring paths remain
disabled.

The source was validated on macOS with release tests, Clang static analysis,
ASan/UBSan, PO4, CCM, and CD-MUSIC workloads. The generated Windows DLL must
still be tested with the representative PhreeFit PO4 workload on Windows before
public release.

If the script reports that no C++ build tools were found, open Visual Studio
Installer, modify the installed Visual Studio instance, and install **Desktop
development with C++**, **MSVC v143 x64/x86 build tools**, and a Windows SDK.
