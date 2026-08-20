"""Build src_new.main_cal as a Cython extension for the staged application."""

import os
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup


project_root = Path(__file__).resolve().parents[2]
source_dir = Path(os.environ.get("PHREEFIT_SOURCE_DIR", project_root / "src_new"))

setup(
    name="phreefit-main-cal",
    ext_modules=cythonize(
        [Extension("src_new.main_cal", [str(source_dir / "main_cal.py")])],
        annotate=False,
        build_dir=os.environ.get("PHREEFIT_CYTHON_BUILD_DIR"),
        compiler_directives={"language_level": "3"},
    ),
)
