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
architecture = platform.machine()
if architecture != "arm64":
    raise RuntimeError(
        "The packaged optimized IPhreeqc 3.8.6 library is currently available "
        f"only for macOS arm64, not {architecture}."
    )

extension_files = sorted(source_dir.glob("main_cal*.so"))
if not extension_files:
    raise FileNotFoundError(
        f"Compiled main_cal extension not found in {source_dir}. "
        "Run packaging/macos/build_macos.sh instead of invoking this spec directly."
    )

iphreeqc_lib = Path(
    os.environ.get(
        "PHREEFIT_IPHREEQC_LIBRARY",
        project_root / "packaging" / "lib" / "libiphreeqc-3.8.6.dylib",
    )
).resolve()
if not iphreeqc_lib.is_file():
    raise FileNotFoundError(f"Optimized IPhreeqc 3.8.6 library not found: {iphreeqc_lib}")

a = Analysis(
    [str(source_dir / "PhreeFit.py")],
    pathex=[str(source_dir.parent)],
    binaries=[
        (str(extension_files[0]), "src_new"),
        (str(iphreeqc_lib), "iphreeqc"),
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
    runtime_hooks=[str(project_root / "packaging" / "runtime_iphreeqc.py")],
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
    target_arch=architecture,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    name="PhreeFit",
)

app = BUNDLE(
    coll,
    name="PhreeFit.app",
    bundle_identifier="org.phreefit.PhreeFit",
    target_arch=architecture,
    info_plist={
        "CFBundleDisplayName": "PhreeFit",
        "CFBundleName": "PhreeFit",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "LSMinimumSystemVersion": "11.0",
        "NSHighResolutionCapable": True,
    },
)
