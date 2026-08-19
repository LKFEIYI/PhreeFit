#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR:h:h}
BUILD_ROOT="$PROJECT_ROOT/build/macos"
STAGE_ROOT="$BUILD_ROOT/stage"
STAGE_SOURCE="$STAGE_ROOT/src_new"
DIST_ROOT="$PROJECT_ROOT/dist/macos"
VERSION=${PHREEFIT_VERSION:-}
APP_PATH="$DIST_ROOT/PhreeFit.app"

if [[ "$BUILD_ROOT" != "$PROJECT_ROOT/build/macos" || "$DIST_ROOT" != "$PROJECT_ROOT/dist/macos" ]]; then
    print -u2 "Refusing to clean unexpected build paths."
    exit 1
fi

PYTHON_BIN=${PHREEFIT_PYTHON:-}
if [[ -z "$PYTHON_BIN" ]]; then
    PYTHON_BIN=$(command -v python3 || true)
fi
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
    print -u2 "Python not found. Set PHREEFIT_PYTHON to the build-environment Python."
    exit 1
fi

SOURCE_VERSION=$("$PYTHON_BIN" -c \
    'import runpy, sys; print(runpy.run_path(sys.argv[1])["__version__"])' \
    "$PROJECT_ROOT/src_new/version.py")
if [[ -z "$VERSION" ]]; then
    VERSION="$SOURCE_VERSION"
elif [[ "$VERSION" != "$SOURCE_VERSION" ]]; then
    print -u2 "PHREEFIT_VERSION ($VERSION) does not match src_new/version.py ($SOURCE_VERSION)."
    exit 1
fi
DMG_PATH="$DIST_ROOT/PhreeFit-$VERSION-$(uname -m).dmg"

"$PYTHON_BIN" -c 'import Cython, PyInstaller, PySide6, numpy, scipy, pyqtgraph, phreeqpy' || {
    print -u2 "Missing build dependencies in: $PYTHON_BIN"
    print -u2 "Install: pyinstaller cython setuptools pyside6 numpy scipy pyqtgraph phreeqpy"
    exit 1
}

rm -rf "$BUILD_ROOT" "$DIST_ROOT"
mkdir -p "$STAGE_SOURCE" "$DIST_ROOT"
/usr/bin/rsync -a \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    --exclude 'main_cal.c' \
    --exclude 'main_cal*.so' \
    "$PROJECT_ROOT/src_new/" "$STAGE_SOURCE/"

export PHREEFIT_SOURCE_DIR="$STAGE_SOURCE"
export PHREEFIT_CYTHON_BUILD_DIR="$BUILD_ROOT/cython"
export PHREEFIT_VERSION="$VERSION"
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

if [[ -n ${PHREEFIT_SIGN_IDENTITY:-} ]]; then
    /usr/bin/codesign --force --deep --options runtime --timestamp \
        --sign "$PHREEFIT_SIGN_IDENTITY" "$APP_PATH"
    /usr/bin/codesign --verify --deep --strict --verbose=2 "$APP_PATH"
else
    print "No PHREEFIT_SIGN_IDENTITY set; creating an unsigned test build."
fi

DMG_STAGE="$BUILD_ROOT/dmg"
mkdir -p "$DMG_STAGE"
/usr/bin/ditto "$APP_PATH" "$DMG_STAGE/PhreeFit.app"
/bin/ln -s /Applications "$DMG_STAGE/Applications"
/usr/bin/hdiutil create -ov -format UDZO -volname "PhreeFit $VERSION" \
    -srcfolder "$DMG_STAGE" "$DMG_PATH"

if [[ -n ${PHREEFIT_SIGN_IDENTITY:-} ]]; then
    /usr/bin/codesign --force --timestamp --sign "$PHREEFIT_SIGN_IDENTITY" "$DMG_PATH"
fi

print "Application: $APP_PATH"
print "Disk image:  $DMG_PATH"
