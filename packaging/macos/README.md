# PhreeFit macOS packaging

This build uses `src_new` as its only application source. It follows the old
`PhreeFit-lean.spec`, but removes its fixed source path and detects the current
Mac architecture and matching IPhreeqc library.

## Build an app and DMG

Use an arm64 Python environment on Apple Silicon, or an x86_64 environment on
an Intel Mac. All native dependencies must have the same architecture.

The release version is read from `src_new/version.py`; update that file before
building a new release. `PHREEFIT_VERSION` is optional and, when supplied, must
match the version in that file.

```bash
export PHREEFIT_PYTHON=/Users/lyt/conda/miniconda3/envs/pf_compile/bin/python
./packaging/macos/build_macos.sh
```

Output:

- `dist/macos/PhreeFit.app`
- `dist/macos/PhreeFit-<version>-<architecture>.dmg`

The script copies `src_new` to `build/macos/stage` before compiling Cython, so
generated C and extension files do not modify the source tree.

## Local verification

```bash
open dist/macos/PhreeFit.app
codesign --verify --deep --strict --verbose=2 dist/macos/PhreeFit.app
spctl --assess --type execute --verbose=4 dist/macos/PhreeFit.app
```

An unsigned build is suitable for testing on the build Mac. Public releases
should be signed with a `Developer ID Application` certificate and notarized.

## Signed build

```bash
export PHREEFIT_PYTHON=/Users/lyt/conda/miniconda3/envs/pf_compile/bin/python
export PHREEFIT_SIGN_IDENTITY='Developer ID Application: Your Name (TEAMID)'
./packaging/macos/build_macos.sh
```

Create a reusable notarization credential once:

```bash
xcrun notarytool store-credentials PhreeFit-notary \
  --apple-id 'you@example.com' \
  --team-id 'TEAMID' \
  --password 'APP_SPECIFIC_PASSWORD'
```

Then submit and staple the generated DMG:

```bash
xcrun notarytool submit dist/macos/PhreeFit-1.0.0-arm64.dmg \
  --keychain-profile PhreeFit-notary --wait
xcrun stapler staple dist/macos/PhreeFit-1.0.0-arm64.dmg
spctl --assess --type open --context context:primary-signature --verbose=4 \
  dist/macos/PhreeFit-1.0.0-arm64.dmg
```

To support both Intel and Apple Silicon, build and test separately on matching
Python environments. The bundled `phreeqpy` libraries are architecture-specific;
do not label a single-architecture build as universal.
