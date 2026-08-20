# PhreeFit macOS packaging

This build uses `src_new` as its only application source and bundles PhreeFit's
optimized IPhreeqc 3.8.6 library from
`packaging/lib/libiphreeqc-3.8.6.dylib`. The packaged application selects this
library explicitly instead of using phreeqpy's bundled IPhreeqc 3.7.3 library.

## Build an app and DMG

The current optimized library is arm64, so the build requires an arm64 Python
environment on Apple Silicon. All native dependencies must have the same
architecture. The script checks the library architecture before building.

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

To test another compatible 3.8.6 build without replacing the default file,
set `PHREEFIT_IPHREEQC_LIBRARY` to its absolute path before invoking the build
script. The selected library is bundled as
`Contents/Frameworks/iphreeqc/libiphreeqc-3.8.6.dylib` and a PyInstaller
runtime hook sets the path used by `main_cal`.

The bundled binary includes one-step CD-MUSIC Modified Newton reuse, reduced
activity-coefficient recomputation in numerical Jacobians, and supported local
analytic CD-MUSIC potential columns. Exact activation/fallback conditions,
performance results, SHA-256, and memory-safety validation are documented in
`packaging/lib/README.md`.

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

An Intel package requires a separately compiled and tested x86_64 version of
the optimized IPhreeqc library; do not label this arm64 build as universal.
