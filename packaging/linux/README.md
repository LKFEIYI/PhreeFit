# PhreeFit Linux packaging

This build uses `src_new` as its only application source. It first compiles the
project's modified IPhreeqc 3.8.6 source with GCC, then compiles
`src_new.main_cal`, bundles the custom shared library, creates a portable
`tar.gz`, and optionally creates a Debian package.

The IPhreeqc source of record is:

```text
iphreeqc/iphreeqc-3.8.6-17100
```

The build does not use the Linux IPhreeqc 3.7.3 binary shipped by `phreeqpy`.
Because `phreeqpy.iphreeqc.phreeqc_dll` hard-codes its Linux runtime filenames,
the compiled 3.8.6 library is placed in the frozen application under that
compatibility filename. Its binary contents still come from the modified 3.8.6
source tree.

Supported build architectures:

- `x86_64` (`amd64` Debian package)
- `aarch64` (`arm64` Debian package)

Linux binaries are not generally portable to systems with an older glibc than
the build machine. Build on the oldest Linux distribution that you intend to
support; Ubuntu 22.04 is a practical baseline for current Qt 6 builds.

## System dependencies

Debian/Ubuntu example:

```bash
sudo apt update
sudo apt install -y \
  build-essential cmake python3-dev python3-venv rsync \
  libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0
```

Create a clean Python environment:

```bash
python3 -m venv .venv-build
source .venv-build/bin/activate
python -m pip install --upgrade pip
python -m pip install -r packaging/linux/requirements-build.txt
```

## Build

From the project root:

```bash
PHREEFIT_PYTHON="$PWD/.venv-build/bin/python" \
./packaging/linux/build_linux.sh
```

The version is read from `src_new/version.py`. If `PHREEFIT_VERSION` is set, it
must match the source version.

The build performs these native compilation steps automatically:

1. Configure the modified IPhreeqc source with CMake, GCC/G++, shared-library
   mode, Release optimization, and tests disabled.
2. Build the `IPhreeqc` shared-library target.
3. Load the resulting library and verify its `CreateIPhreeqc` ABI symbol.
4. Compile `src_new.main_cal` with Cython and GCC.
5. Freeze the application with the custom IPhreeqc library.

Outputs on x86_64:

- `dist/linux/PhreeFit/PhreeFit`
- `dist/linux/PhreeFit-<version>-linux-x86_64.tar.gz`
- `dist/linux/phreefit_<version>_amd64.deb` when `dpkg-deb` is available

To use a custom GCC toolchain:

```bash
PHREEFIT_PYTHON="$PWD/.venv-build/bin/python" \
PHREEFIT_CC=gcc-13 \
PHREEFIT_CXX=g++-13 \
./packaging/linux/build_linux.sh
```

To skip the Debian package:

```bash
PHREEFIT_SKIP_DEB=1 \
PHREEFIT_PYTHON="$PWD/.venv-build/bin/python" \
./packaging/linux/build_linux.sh
```

## Manual verification

Run the unpacked application:

```bash
./dist/linux/PhreeFit/PhreeFit
```

Install the Debian package:

```bash
sudo apt install ./dist/linux/phreefit_<version>_amd64.deb
phreefit
```

Verify on a clean target machine without Python installed. Test database and
CSV loading, both optimization modes, PNG/SVG export, settings/history, and
desktop launching. If Qt reports an `xcb` platform-plugin error, inspect the
missing system library with `ldd` rather than copying libraries from a newer
distribution.
