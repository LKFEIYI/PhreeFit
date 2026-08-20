#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)
BUILD_ROOT="$PROJECT_ROOT/build/linux"
STAGE_ROOT="$BUILD_ROOT/stage"
STAGE_SOURCE="$STAGE_ROOT/src_new"
IPHREEQC_SOURCE="$PROJECT_ROOT/iphreeqc/iphreeqc-3.8.6-17100"
IPHREEQC_BUILD="$BUILD_ROOT/iphreeqc-build"
IPHREEQC_RUNTIME_DIR="$BUILD_ROOT/iphreeqc-runtime"
DIST_ROOT="$PROJECT_ROOT/dist/linux"
APP_DIR="$DIST_ROOT/PhreeFit"
VERSION=${PHREEFIT_VERSION:-}
PYTHON_BIN=${PHREEFIT_PYTHON:-python3}
CC_BIN=${PHREEFIT_CC:-gcc}
CXX_BIN=${PHREEFIT_CXX:-g++}

case "$(uname -m)" in
    x86_64|amd64)
        PACKAGE_ARCH=x86_64
        DEB_ARCH=amd64
        IPHREEQC_RUNTIME_NAME=libiphreeqc-3.7.3.so
        ;;
    aarch64|arm64)
        PACKAGE_ARCH=aarch64
        DEB_ARCH=arm64
        IPHREEQC_RUNTIME_NAME=linux_arm_libiphreeqc-3.7.3.so
        ;;
    *)
        printf 'Unsupported Linux architecture: %s\n' "$(uname -m)" >&2
        exit 1
        ;;
esac

if [[ "$BUILD_ROOT" != "$PROJECT_ROOT/build/linux" || "$DIST_ROOT" != "$PROJECT_ROOT/dist/linux" ]]; then
    printf 'Refusing to clean unexpected build paths.\n' >&2
    exit 1
fi

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
    printf 'Python not found: %s\n' "$PYTHON_BIN" >&2
    exit 1
}
command -v "$CC_BIN" >/dev/null 2>&1 || {
    printf 'C compiler not found: %s\n' "$CC_BIN" >&2
    exit 1
}
command -v "$CXX_BIN" >/dev/null 2>&1 || {
    printf 'C++ compiler not found: %s\n' "$CXX_BIN" >&2
    exit 1
}
command -v cmake >/dev/null 2>&1 || {
    printf 'CMake 3.20 or newer is required.\n' >&2
    exit 1
}
if [[ ! -f "$IPHREEQC_SOURCE/CMakeLists.txt" ]]; then
    printf 'Modified IPhreeqc source not found: %s\n' "$IPHREEQC_SOURCE" >&2
    exit 1
fi

PYTHON_ARCH=$(
    "$PYTHON_BIN" -c 'import platform, struct; print(f"{platform.machine().lower()}:{struct.calcsize(chr(80)) * 8}")'
)
case "$PACKAGE_ARCH:$PYTHON_ARCH" in
    x86_64:x86_64:64|x86_64:amd64:64|aarch64:aarch64:64|aarch64:arm64:64) ;;
    *)
        printf 'A native %s 64-bit Python is required; detected %s.\n' \
            "$PACKAGE_ARCH" "$PYTHON_ARCH" >&2
        exit 1
        ;;
esac

SOURCE_VERSION=$(
    "$PYTHON_BIN" -c \
        'import runpy, sys; print(runpy.run_path(sys.argv[1])["__version__"])' \
        "$PROJECT_ROOT/src_new/version.py"
)
if [[ -z "$VERSION" ]]; then
    VERSION="$SOURCE_VERSION"
elif [[ "$VERSION" != "$SOURCE_VERSION" ]]; then
    printf 'PHREEFIT_VERSION (%s) does not match src_new/version.py (%s).\n' \
        "$VERSION" "$SOURCE_VERSION" >&2
    exit 1
fi

"$PYTHON_BIN" -c 'import Cython, PyInstaller, PySide6, numpy, scipy, pyqtgraph, phreeqpy' || {
    printf 'Missing Python build dependencies. Install packaging/linux/requirements-build.txt.\n' >&2
    exit 1
}

TAR_PATH="$DIST_ROOT/PhreeFit-$VERSION-linux-$PACKAGE_ARCH.tar.gz"
DEB_PATH="$DIST_ROOT/phreefit_${VERSION}_${DEB_ARCH}.deb"

rm -rf "$BUILD_ROOT"
rm -rf "$APP_DIR"
rm -f "$TAR_PATH" "$DEB_PATH"
mkdir -p "$STAGE_SOURCE" "$DIST_ROOT"

if command -v nproc >/dev/null 2>&1; then
    DEFAULT_JOBS=$(nproc)
else
    DEFAULT_JOBS=1
fi
BUILD_JOBS=${PHREEFIT_JOBS:-$DEFAULT_JOBS}

cmake \
    -S "$IPHREEQC_SOURCE" \
    -B "$IPHREEQC_BUILD" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER="$CC_BIN" \
    -DCMAKE_CXX_COMPILER="$CXX_BIN" \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTING=OFF
cmake --build "$IPHREEQC_BUILD" \
    --config Release \
    --parallel "$BUILD_JOBS" \
    --target IPhreeqc

IPHREEQC_COMPILED_LIB=$(find "$IPHREEQC_BUILD" -type f -name 'libIPhreeqc.so*' -print -quit)
if [[ -z "$IPHREEQC_COMPILED_LIB" ]]; then
    printf 'Compiled IPhreeqc shared library was not found under %s.\n' \
        "$IPHREEQC_BUILD" >&2
    exit 1
fi
"$PYTHON_BIN" -c \
    'import ctypes, sys; library = ctypes.CDLL(sys.argv[1]); getattr(library, "CreateIPhreeqc")' \
    "$IPHREEQC_COMPILED_LIB"

mkdir -p "$IPHREEQC_RUNTIME_DIR"
cp "$IPHREEQC_COMPILED_LIB" "$IPHREEQC_RUNTIME_DIR/$IPHREEQC_RUNTIME_NAME"

rsync -a \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    --exclude 'main_cal.c' \
    --exclude 'main_cal*.so' \
    --exclude 'main_cal*.pyd' \
    "$PROJECT_ROOT/src_new/" "$STAGE_SOURCE/"

export CC="$CC_BIN"
export CXX="$CXX_BIN"
export PHREEFIT_SOURCE_DIR="$STAGE_SOURCE"
export PHREEFIT_VERSION="$VERSION"
export PHREEFIT_IPHREEQC_LIB="$IPHREEQC_RUNTIME_DIR/$IPHREEQC_RUNTIME_NAME"
export PYINSTALLER_CONFIG_DIR="$BUILD_ROOT/pyinstaller-config"

"$PYTHON_BIN" "$SCRIPT_DIR/setup_main_cal.py" build_ext \
    --build-lib "$STAGE_ROOT" \
    --build-temp "$BUILD_ROOT/cython-temp"

"$PYTHON_BIN" -m PyInstaller \
    --clean \
    --noconfirm \
    --workpath "$BUILD_ROOT/pyinstaller" \
    --distpath "$DIST_ROOT" \
    "$SCRIPT_DIR/PhreeFit.spec"

tar -C "$DIST_ROOT" -czf "$TAR_PATH" PhreeFit
printf 'Portable archive: %s\n' "$TAR_PATH"

if [[ ${PHREEFIT_SKIP_DEB:-0} != 1 ]] && command -v dpkg-deb >/dev/null 2>&1; then
    DEB_ROOT="$BUILD_ROOT/deb"
    mkdir -p \
        "$DEB_ROOT/DEBIAN" \
        "$DEB_ROOT/opt/phreefit" \
        "$DEB_ROOT/usr/bin" \
        "$DEB_ROOT/usr/share/applications"
    cp -a "$APP_DIR/." "$DEB_ROOT/opt/phreefit/"
    ln -s /opt/phreefit/PhreeFit "$DEB_ROOT/usr/bin/phreefit"

    cat > "$DEB_ROOT/DEBIAN/control" <<EOF
Package: phreefit
Version: $VERSION
Section: science
Priority: optional
Architecture: $DEB_ARCH
Maintainer: PhreeFit
Depends: libc6, libegl1, libgl1, libxkbcommon-x11-0, libxcb-cursor0
Description: PhreeFit chemical fitting application
 PhreeFit provides a Qt desktop interface for PHREEQC-based fitting and
 optimization workflows.
EOF

    cat > "$DEB_ROOT/usr/share/applications/org.phreefit.PhreeFit.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=PhreeFit
Comment=PHREEQC-based fitting and optimization
Exec=/opt/phreefit/PhreeFit
Terminal=false
Categories=Science;Education;
EOF

    dpkg-deb --root-owner-group --build "$DEB_ROOT" "$DEB_PATH"
    printf 'Debian package:  %s\n' "$DEB_PATH"
else
    printf 'Skipping .deb package (dpkg-deb unavailable or PHREEFIT_SKIP_DEB=1).\n'
fi

printf 'Application:     %s\n' "$APP_DIR"
