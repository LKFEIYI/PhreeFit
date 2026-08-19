# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

from PyInstaller.utils.hooks import get_module_file_attribute


project_root = Path(SPECPATH).resolve().parents[1]
source_dir = Path(os.environ.get("PHREEFIT_SOURCE_DIR", project_root / "src_new")).resolve()

extension_files = sorted(source_dir.glob("main_cal*.pyd"))
if not extension_files:
    raise FileNotFoundError(
        f"Compiled main_cal extension not found in {source_dir}. "
        "Run packaging\\windows\\build_windows.ps1 instead of invoking this spec directly."
    )

phreeqpy_dir = Path(get_module_file_attribute("phreeqpy")).parent
iphreeqc_lib = phreeqpy_dir / "iphreeqc" / "phreeqc3" / "IPhreeqc-3.7.3.dll"
if not iphreeqc_lib.is_file():
    raise FileNotFoundError(f"IPhreeqc library not found: {iphreeqc_lib}")

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
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PhreeFit",
)
