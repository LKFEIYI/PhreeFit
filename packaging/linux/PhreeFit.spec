# -*- mode: python ; coding: utf-8 -*-
import os
import platform
from pathlib import Path
import runpy

project_root = Path(SPECPATH).resolve().parents[1]
source_dir = Path(os.environ.get("PHREEFIT_SOURCE_DIR", project_root / "src_new")).resolve()
source_version = runpy.run_path(str(source_dir / "version.py"))["__version__"]
version = os.environ.get("PHREEFIT_VERSION", source_version)
if version != source_version:
    raise ValueError(
        f"PHREEFIT_VERSION ({version}) does not match src_new/version.py ({source_version})."
    )

machine = platform.machine().lower()
iphreeqc_runtime_name = {
    "x86_64": "libiphreeqc-3.7.3.so",
    "amd64": "libiphreeqc-3.7.3.so",
    "aarch64": "linux_arm_libiphreeqc-3.7.3.so",
    "arm64": "linux_arm_libiphreeqc-3.7.3.so",
}.get(machine)
if iphreeqc_runtime_name is None:
    raise RuntimeError(f"Unsupported Linux architecture: {machine}")

extension_files = sorted(source_dir.glob("main_cal*.so"))
if not extension_files:
    raise FileNotFoundError(
        f"Compiled main_cal extension not found in {source_dir}. "
        "Run packaging/linux/build_linux.sh instead of invoking this spec directly."
    )

iphreeqc_lib = Path(
    os.environ.get(
        "PHREEFIT_IPHREEQC_LIB",
        project_root / "build" / "linux" / "iphreeqc-runtime" / iphreeqc_runtime_name,
    )
).resolve()
if not iphreeqc_lib.is_file():
    raise FileNotFoundError(
        f"Custom IPhreeqc library not found: {iphreeqc_lib}. "
        "Run packaging/linux/build_linux.sh to compile the project source first."
    )

a = Analysis(
    [str(source_dir / "PhreeFit.py")],
    pathex=[str(source_dir.parent)],
    binaries=[
        (str(extension_files[0]), "src_new"),
        (str(iphreeqc_lib), "phreeqpy/iphreeqc/phreeqc3"),
    ],
    datas=[],
    hiddenimports=[
        "phreeqpy.iphreeqc.phreeqc_dll",
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
        "pyqtgraph.exporters",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["Cython", "cython", "pyqtgraph.examples", "pyqtgraph.opengl"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PhreeFit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    name="PhreeFit",
)
