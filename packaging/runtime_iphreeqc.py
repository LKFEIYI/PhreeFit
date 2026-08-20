"""Select PhreeFit's bundled IPhreeqc 3.8.6 library at application startup."""

import os
from pathlib import Path
import sys


if "PHREEFIT_IPHREEQC_LIBRARY" not in os.environ:
    if sys.platform == "darwin":
        library_name = "libiphreeqc-3.8.6.dylib"
    elif sys.platform == "win32":
        library_name = "IPhreeqc-3.8.6.dll"
    else:
        raise RuntimeError(f"Unsupported packaged IPhreeqc platform: {sys.platform}")

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    library = bundle_root / "iphreeqc" / library_name
    if not library.is_file():
        raise FileNotFoundError(f"Bundled IPhreeqc 3.8.6 library not found: {library}")
    os.environ["PHREEFIT_IPHREEQC_LIBRARY"] = str(library)
