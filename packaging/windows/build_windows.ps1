[CmdletBinding()]
param(
    [string]$Version = "",
    [string]$Python = "python",
    [string]$IPhreeqcDll = "",
    [string]$InnoSetupCompiler = "",
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\.."))
$BuildRoot = Join-Path $ProjectRoot "build\windows"
$StageRoot = Join-Path $BuildRoot "stage"
$StageSource = Join-Path $StageRoot "src_new"
$DistRoot = Join-Path $ProjectRoot "dist\windows"
$PortableDir = Join-Path $DistRoot "PhreeFit"
$IPhreeqcSource = Join-Path $ProjectRoot "iphreeqc\iphreeqc-3.8.6-17100"
$PackagedIPhreeqcDll = Join-Path $ProjectRoot "packaging\lib\IPhreeqc-3.8.6.dll"
$SourceVersion = & $Python -c "import runpy, sys; print(runpy.run_path(sys.argv[1])['__version__'])" `
    (Join-Path $ProjectRoot "src_new\version.py")
if ($LASTEXITCODE -ne 0 -or -not $SourceVersion) {
    throw "Unable to read the version from src_new\version.py."
}
if (-not $Version) {
    $Version = $SourceVersion
}
elseif ($Version -ne $SourceVersion) {
    throw "Requested version '$Version' does not match src_new\version.py ('$SourceVersion')."
}
$ZipPath = Join-Path $DistRoot "PhreeFit-$Version-win-x64.zip"

if ($BuildRoot -ne (Join-Path $ProjectRoot "build\windows") -or
    $DistRoot -ne (Join-Path $ProjectRoot "dist\windows")) {
    throw "Refusing to clean unexpected build paths."
}

& $Python -c "import Cython, PyInstaller, PySide6, numpy, scipy, pyqtgraph, phreeqpy"
if ($LASTEXITCODE -ne 0) {
    throw "Missing build dependencies in '$Python'. See packaging\windows\requirements-build.txt."
}

if (Test-Path $BuildRoot) { Remove-Item -Recurse -Force $BuildRoot }
if (Test-Path $DistRoot) { Remove-Item -Recurse -Force $DistRoot }
New-Item -ItemType Directory -Force $StageSource, $DistRoot | Out-Null

if ($IPhreeqcDll) {
    $ResolvedIPhreeqcDll = [System.IO.Path]::GetFullPath($IPhreeqcDll)
    if (-not (Test-Path -PathType Leaf $ResolvedIPhreeqcDll)) {
        throw "Specified optimized IPhreeqc 3.8.6 DLL not found: $ResolvedIPhreeqcDll"
    }
}
elseif (Test-Path -PathType Leaf $PackagedIPhreeqcDll) {
    $ResolvedIPhreeqcDll = $PackagedIPhreeqcDll
}
else {
    if (-not (Test-Path -PathType Container $IPhreeqcSource)) {
        throw "IPhreeqc 3.8.6 source not found: $IPhreeqcSource. Provide -IPhreeqcDll with an optimized x64 DLL."
    }
    & cmake --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "CMake is required to build the optimized IPhreeqc 3.8.6 DLL."
    }

    $IPhreeqcBuild = Join-Path $BuildRoot "iphreeqc"
    & cmake -S $IPhreeqcSource -B $IPhreeqcBuild -A x64 `
        -DBUILD_SHARED_LIBS=ON `
        -DIPHREEQC_ENABLE_MODULE=OFF `
        -DIPHREEQC_FORTRAN_TESTING=OFF
    if ($LASTEXITCODE -ne 0) { throw "IPhreeqc 3.8.6 CMake configuration failed." }

    & cmake --build $IPhreeqcBuild --config Release --target IPhreeqc
    if ($LASTEXITCODE -ne 0) { throw "IPhreeqc 3.8.6 Release build failed." }

    $BuiltDll = Get-ChildItem -Path $IPhreeqcBuild -Recurse -File -Filter "IPhreeqc.dll" |
        Where-Object { $_.FullName -match "[\\/]Release[\\/]" } |
        Select-Object -First 1
    if (-not $BuiltDll) {
        throw "The IPhreeqc build completed but IPhreeqc.dll was not found."
    }
    $ResolvedIPhreeqcDll = $BuiltDll.FullName
}

# CMake names its output IPhreeqc.dll. Give every selected build the stable
# versioned name expected by the runtime hook before handing it to PyInstaller.
$NativeStage = Join-Path $BuildRoot "native"
New-Item -ItemType Directory -Force $NativeStage | Out-Null
$VersionedIPhreeqcDll = Join-Path $NativeStage "IPhreeqc-3.8.6.dll"
Copy-Item -Force $ResolvedIPhreeqcDll $VersionedIPhreeqcDll
$ResolvedIPhreeqcDll = $VersionedIPhreeqcDll

& robocopy (Join-Path $ProjectRoot "src_new") $StageSource /E /NFL /NDL /NJH /NJS /NP `
    /XD "__pycache__" /XF ".DS_Store" "main_cal.c" "main_cal*.so" "main_cal*.pyd"
if ($LASTEXITCODE -gt 7) {
    throw "Failed to stage src_new (robocopy exit code $LASTEXITCODE)."
}

$env:PHREEFIT_SOURCE_DIR = $StageSource
$env:PHREEFIT_VERSION = $Version
$env:PHREEFIT_IPHREEQC_LIBRARY = $ResolvedIPhreeqcDll
$env:PYINSTALLER_CONFIG_DIR = Join-Path $BuildRoot "pyinstaller-config"

& $Python (Join-Path $ScriptDir "setup_main_cal.py") build_ext `
    --build-lib $StageRoot `
    --build-temp (Join-Path $BuildRoot "cython-temp")
if ($LASTEXITCODE -ne 0) { throw "Cython extension build failed." }

& $Python -m PyInstaller `
    --clean `
    --noconfirm `
    --workpath (Join-Path $BuildRoot "pyinstaller") `
    --distpath $DistRoot `
    (Join-Path $ScriptDir "PhreeFit.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Compress-Archive -Path $PortableDir -DestinationPath $ZipPath -CompressionLevel Optimal
Write-Host "Portable package: $ZipPath"

if (-not $SkipInstaller) {
    $Iscc = $InnoSetupCompiler
    if (-not $Iscc) {
        $Candidates = @(
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
        )
        $Iscc = $Candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    }

    if ($Iscc -and (Test-Path $Iscc)) {
        & $Iscc "/DMyAppVersion=$Version" "/DSourceDir=$PortableDir" `
            "/DOutputDir=$DistRoot" (Join-Path $ScriptDir "PhreeFit.iss")
        if ($LASTEXITCODE -ne 0) { throw "Inno Setup build failed." }
        Write-Host "Installer: $(Join-Path $DistRoot "PhreeFit-$Version-win-x64-setup.exe")"
    }
    else {
        Write-Warning "Inno Setup 6 was not found. ZIP was created; install Inno Setup and rerun to create Setup.exe."
    }
}

Write-Host "Application folder: $PortableDir"
