@echo off
setlocal
cd /d "%~dp0"

where cl.exe >nul 2>nul
if errorlevel 1 call :initialize_msvc
if errorlevel 1 (
    echo.
    echo ERROR: The Visual Studio x64 C/C++ compiler environment could not be initialized.
    echo Install "Desktop development with C++" and the MSVC v143 x64/x86 build tools.
    pause
    exit /b 1
)

where cl.exe >nul 2>nul
if errorlevel 1 (
    echo ERROR: cl.exe is still unavailable after initializing Visual Studio.
    pause
    exit /b 1
)

echo Using MSVC compiler:
where cl.exe

where powershell.exe >nul 2>nul
if errorlevel 1 (
    echo ERROR: Windows PowerShell was not found.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_iphreeqc_dll.ps1" %*
set "BUILD_EXIT=%ERRORLEVEL%"

if not "%BUILD_EXIT%"=="0" (
    echo.
    echo IPhreeqc DLL build failed. Review the error above.
) else (
    echo.
    echo IPhreeqc DLL build completed successfully.
)

pause
exit /b %BUILD_EXIT%

:initialize_msvc
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
    echo ERROR: Visual Studio Installer's vswhere.exe was not found:
    echo        %VSWHERE%
    exit /b 1
)

set "VS_INSTALL_PATH="
for /f "usebackq tokens=*" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VS_INSTALL_PATH=%%I"

if not defined VS_INSTALL_PATH (
    echo ERROR: No Visual Studio installation with the x64/x86 C++ build tools was found.
    exit /b 1
)

set "VSDEVCMD=%VS_INSTALL_PATH%\Common7\Tools\VsDevCmd.bat"
if not exist "%VSDEVCMD%" (
    echo ERROR: VsDevCmd.bat was not found:
    echo        %VSDEVCMD%
    exit /b 1
)

echo Initializing Visual Studio x64 build environment:
echo   %VS_INSTALL_PATH%
call "%VSDEVCMD%" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 (
    echo ERROR: VsDevCmd.bat failed.
    exit /b 1
)
exit /b 0
