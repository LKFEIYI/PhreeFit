[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$DisableLto,
    [string]$WorkRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = $PSScriptRoot
$BundledSource = Join-Path $ScriptDir "source"
$RepositorySource = [System.IO.Path]::GetFullPath(
    (Join-Path $ScriptDir "..\..\..\iphreeqc\iphreeqc-3.8.6-17100")
)

if (Test-Path -PathType Leaf (Join-Path $BundledSource "CMakeLists.txt")) {
    $SourceDir = $BundledSource
}
elseif (Test-Path -PathType Leaf (Join-Path $RepositorySource "CMakeLists.txt")) {
    # This fallback lets the checked-in helper run before a source ZIP is made.
    $SourceDir = $RepositorySource
}
else {
    throw "Optimized IPhreeqc source was not found beside this script. Re-extract the complete source package."
}

$OutputDir = Join-Path $ScriptDir "output\win-x64"

if (-not $WorkRoot) {
    $TemporaryBase = $env:TEMP
    if (-not $TemporaryBase) { $TemporaryBase = $env:LOCALAPPDATA }
    if (-not $TemporaryBase) {
        throw "Neither TEMP nor LOCALAPPDATA is defined. Supply a short path with -WorkRoot C:\ipq386."
    }
    $WorkRoot = Join-Path $TemporaryBase "PhreeFit-IPhreeqc386"
}
$WorkRoot = [System.IO.Path]::GetFullPath($WorkRoot)
$StagedSource = Join-Path $WorkRoot "source"
$BuildDir = Join-Path $WorkRoot "build-x64-release"

$PathTrimCharacters = [char[]]"\/"
$SourcePathForCheck = [System.IO.Path]::GetFullPath($SourceDir).TrimEnd($PathTrimCharacters)
$StagePathForCheck = [System.IO.Path]::GetFullPath($StagedSource).TrimEnd($PathTrimCharacters)
if ($SourcePathForCheck -eq $StagePathForCheck -or
    $StagePathForCheck.StartsWith($SourcePathForCheck + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
    $SourcePathForCheck.StartsWith($StagePathForCheck + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The temporary staging directory must not overlap the source directory. Choose another -WorkRoot."
}

if ($BuildDir.Length -gt 150) {
    throw "The temporary build path is still too long: $BuildDir. Rerun with -WorkRoot C:\ipq386."
}

if ($Clean) {
    $ExpectedBuildDir = Join-Path $WorkRoot "build-x64-release"
    $ExpectedOutputDir = Join-Path $ScriptDir "output\win-x64"
    if ($BuildDir -ne $ExpectedBuildDir -or $OutputDir -ne $ExpectedOutputDir) {
        throw "Refusing to clean unexpected directories."
    }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    if (Test-Path $OutputDir) { Remove-Item -Recurse -Force $OutputDir }
}

if (-not (Get-Command cmake.exe -ErrorAction SilentlyContinue)) {
    throw "cmake.exe was not found. Install CMake 3.20+ and select 'Add CMake to PATH'."
}
if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
    throw "cl.exe was not found. Run from a Visual Studio x64 developer environment."
}
if (-not (Get-Command nmake.exe -ErrorAction SilentlyContinue)) {
    throw "nmake.exe was not found. Install the MSVC x64/x86 build tools."
}

$CMakeExe = (Get-Command cmake.exe).Source
$CMakeVersionText = (& $CMakeExe --version | Select-Object -First 1)
if ($LASTEXITCODE -ne 0) { throw "Unable to run cmake.exe." }
Write-Host $CMakeVersionText

# CMake/MSVC object paths have a practical limit near 250 characters. Mirror
# the source into a short disposable location so the package may be extracted
# under a long user/Desktop path without breaking compiler detection.
New-Item -ItemType Directory -Force $WorkRoot, $StagedSource, $OutputDir | Out-Null
Write-Host "Staging source in short work directory: $StagedSource"
& robocopy.exe $SourceDir $StagedSource /MIR /NFL /NDL /NJH /NJS /NP `
    /XD "_build" "__pycache__" /XF ".DS_Store" "*.pyc" "*.o" "*.obj" "*.dylib" "*.so"
$RobocopyExit = $LASTEXITCODE
if ($RobocopyExit -gt 7) {
    throw "Failed to stage the optimized source (robocopy exit code $RobocopyExit)."
}

$ConfigureArgs = @(
    "-S", $StagedSource,
    "-B", $BuildDir,
    "-G", "NMake Makefiles",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DBUILD_SHARED_LIBS=ON",
    "-DBUILD_TESTING=OFF",
    "-DBUILD_CLR_LIBS=OFF",
    "-DIPHREEQC_ENABLE_MODULE=OFF",
    "-DIPHREEQC_FORTRAN_TESTING=OFF"
)
if (-not $DisableLto) {
    $ConfigureArgs += "-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON"
}

Write-Host "Configuring optimized IPhreeqc 3.8.6 (Release, x64)..."
Write-Host "Build directory: $BuildDir"
& $CMakeExe @ConfigureArgs
if ($LASTEXITCODE -ne 0) { throw "CMake configuration failed." }

Write-Host "Building IPhreeqc.dll..."
& $CMakeExe --build $BuildDir --target IPhreeqc --parallel
if ($LASTEXITCODE -ne 0) { throw "IPhreeqc Release build failed." }

$BuiltDll = Get-ChildItem -Path $BuildDir -Recurse -File -Filter "IPhreeqc.dll" |
    Select-Object -First 1
if (-not $BuiltDll) {
    throw "The build succeeded, but IPhreeqc.dll was not found."
}

$UnversionedDll = Join-Path $OutputDir "IPhreeqc.dll"
$VersionedDll = Join-Path $OutputDir "IPhreeqc-3.8.6.dll"
Copy-Item -Force $BuiltDll.FullName $UnversionedDll
Copy-Item -Force $BuiltDll.FullName $VersionedDll

$BuiltImportLibrary = Get-ChildItem -Path $BuildDir -Recurse -File -Filter "IPhreeqc.lib" |
    Select-Object -First 1
if ($BuiltImportLibrary) {
    Copy-Item -Force $BuiltImportLibrary.FullName (Join-Path $OutputDir "IPhreeqc.lib")
}

$BuiltPdb = Get-ChildItem -Path $BuildDir -Recurse -File -Filter "IPhreeqc.pdb" |
    Select-Object -First 1
if ($BuiltPdb) {
    Copy-Item -Force $BuiltPdb.FullName (Join-Path $OutputDir "IPhreeqc.pdb")
}

Copy-Item -Force (Join-Path $StagedSource "src\IPhreeqc.h") $OutputDir
Copy-Item -Force (Join-Path $StagedSource "src\IPhreeqc.hpp") $OutputDir
Copy-Item -Force (Join-Path $StagedSource "src\Var.h") $OutputDir

# Validate that the result is a 64-bit PE DLL before reporting success.
$Stream = [System.IO.File]::OpenRead($UnversionedDll)
try {
    $Reader = New-Object System.IO.BinaryReader($Stream)
    if ($Reader.ReadUInt16() -ne 0x5A4D) { throw "Output is not a valid PE file (missing MZ header)." }
    $Stream.Seek(0x3C, [System.IO.SeekOrigin]::Begin) | Out-Null
    $PeOffset = $Reader.ReadInt32()
    $Stream.Seek($PeOffset, [System.IO.SeekOrigin]::Begin) | Out-Null
    if ($Reader.ReadUInt32() -ne 0x00004550) { throw "Output is not a valid PE file (missing PE header)." }
    $Machine = $Reader.ReadUInt16()
    if ($Machine -ne 0x8664) {
        throw ("Expected an x64 DLL (machine 0x8664), found 0x{0:X4}." -f $Machine)
    }
}
finally {
    $Stream.Dispose()
}

# Check that Windows can load the DLL and that the C API entry points exist.
if (-not ("IPhreeqcDllBuilder.NativeMethods" -as [type])) {
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
namespace IPhreeqcDllBuilder {
    public static class NativeMethods {
        [DllImport("kernel32", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern IntPtr LoadLibrary(string path);
        [DllImport("kernel32", SetLastError = true)]
        public static extern IntPtr GetProcAddress(IntPtr module, string name);
        [DllImport("kernel32", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool FreeLibrary(IntPtr module);
    }
}
"@
}

$Module = [IPhreeqcDllBuilder.NativeMethods]::LoadLibrary($UnversionedDll)
if ($Module -eq [IntPtr]::Zero) {
    $Code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    throw "Windows could not load IPhreeqc.dll (Win32 error $Code). Install the x64 Visual C++ runtime if it is missing."
}
try {
    foreach ($ExportName in @("CreateIPhreeqc", "DestroyIPhreeqc", "LoadDatabase", "RunString")) {
        if ([IPhreeqcDllBuilder.NativeMethods]::GetProcAddress($Module, $ExportName) -eq [IntPtr]::Zero) {
            throw "Required C API export '$ExportName' is missing from IPhreeqc.dll."
        }
    }
}
finally {
    [IPhreeqcDllBuilder.NativeMethods]::FreeLibrary($Module) | Out-Null
}

$Hash = (Get-FileHash -Algorithm SHA256 $UnversionedDll).Hash.ToLowerInvariant()
@(
    "$Hash  IPhreeqc.dll",
    "$Hash  IPhreeqc-3.8.6.dll"
) | Set-Content -Encoding ASCII (Join-Path $OutputDir "SHA256SUMS.txt")

Write-Host ""
Write-Host "Build and validation succeeded."
Write-Host "DLL: $UnversionedDll"
Write-Host "Versioned DLL: $VersionedDll"
Write-Host "SHA-256: $Hash"
