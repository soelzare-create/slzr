@echo off
REM ============================================================
REM  DaranX - one-click Docker Desktop installer for Windows
REM  Double-click this file. It will:
REM    1. ask for Administrator rights (UAC)
REM    2. enable WSL 2 (needed by Docker Desktop)
REM    3. install Docker Desktop (local installer > winget > download)
REM    4. add the current user to the "docker-users" group
REM    5. offer to restart Windows
REM  Safe to run again: it skips steps that are already done.
REM
REM  No internet access to docker.com (e.g. blocked/sanctioned)?
REM  Put "Docker Desktop Installer.exe" next to this file and run
REM  it again - the local installer is used and nothing is downloaded.
REM ============================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title DaranX - Docker installer

REM --- 1) Re-launch elevated, passing the real (non-admin) user along ---
net session >nul 2>&1
if errorlevel 1 (
    echo [DaranX] Administrator rights are required. Please accept the UAC prompt...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '\"%USERDOMAIN%\%USERNAME%\"' -Verb RunAs"
    if errorlevel 1 (
        echo [DaranX] ERROR: elevation was cancelled.
        pause
    )
    exit /b
)

set "TARGET_USER=%~1"
if "%TARGET_USER%"=="" set "TARGET_USER=%USERDOMAIN%\%USERNAME%"
set "NEED_REBOOT=0"

echo(
echo ============================================================
echo  DaranX - Docker Desktop installer
echo  User: %TARGET_USER%
echo ============================================================

REM --- Already installed? ---
where docker >nul 2>&1
if not errorlevel 1 goto :already_installed
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" goto :already_installed

REM --- Windows version check (WSL 2 needs build 19041+) ---
for /f %%B in ('powershell -NoProfile -Command "[Environment]::OSVersion.Version.Build"') do set "WINBUILD=%%B"
if not defined WINBUILD set "WINBUILD=99999"
echo [DaranX] Windows build: %WINBUILD%
if %WINBUILD% LSS 19041 (
    echo [DaranX] ERROR: Docker Desktop needs Windows 10 version 2004 ^(build 19041^) or newer.
    echo          Please run Windows Update first, then run this file again.
    goto :end
)

REM --- CPU architecture -> download URL ---
set "ARCH=%PROCESSOR_ARCHITECTURE%"
if defined PROCESSOR_ARCHITEW6432 set "ARCH=%PROCESSOR_ARCHITEW6432%"
if /i "%ARCH%"=="ARM64" (
    set "DD_URL=https://desktop.docker.com/win/main/arm64/Docker%%20Desktop%%20Installer.exe"
) else (
    set "DD_URL=https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe"
)

REM --- 2) Enable WSL 2 ---
echo(
echo [DaranX] Step 1/3: enabling WSL 2...
wsl --status >nul 2>&1
if not errorlevel 1 (
    echo [DaranX] WSL is already enabled. Updating it...
    wsl --update >nul 2>&1
    goto :wsl_done
)
wsl --install --no-distribution
if not errorlevel 1 (
    set "NEED_REBOOT=1"
    goto :wsl_done
)
echo [DaranX] "wsl --install" is not available, enabling Windows features directly...
dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
set "NEED_REBOOT=1"
:wsl_done

REM --- 3) Install Docker Desktop ---
echo(
echo [DaranX] Step 2/3: installing Docker Desktop...
set "INSTALLER="
if exist "%~dp0Docker Desktop Installer.exe" set "INSTALLER=%~dp0Docker Desktop Installer.exe"
if exist "%~dp0DockerDesktopInstaller.exe"   set "INSTALLER=%~dp0DockerDesktopInstaller.exe"
if defined INSTALLER (
    echo [DaranX] Using local installer: "%INSTALLER%"
    goto :run_installer
)

where winget >nul 2>&1
if errorlevel 1 goto :download
echo [DaranX] Installing with winget ^(this can take several minutes^)...
winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --silent
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" goto :installed
echo [DaranX] winget did not finish the install, trying a direct download...

:download
set "INSTALLER=%TEMP%\DockerDesktopInstaller.exe"
echo [DaranX] Downloading Docker Desktop ^(about 500 MB^)...
echo          %DD_URL%
curl.exe -L --fail --retry 3 -o "%INSTALLER%" "%DD_URL%"
if errorlevel 1 (
    echo(
    echo [DaranX] ERROR: download failed.
    echo          docker.com may be blocked on this network. Either:
    echo            - turn on a VPN and run this file again, or
    echo            - download "Docker Desktop Installer.exe" on another
    echo              machine, copy it next to this file, and run it again.
    goto :end
)

:run_installer
echo [DaranX] Running the installer silently ^(this can take several minutes^)...
start "" /wait "%INSTALLER%" install --quiet --accept-license --backend=wsl-2
if not exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    echo [DaranX] ERROR: Docker Desktop was not installed. Try running the installer manually:
    echo          "%INSTALLER%"
    goto :end
)

:installed
set "NEED_REBOOT=1"
echo [DaranX] Docker Desktop installed.

REM --- 4) Allow the user to use Docker ---
echo(
echo [DaranX] Step 3/3: adding %TARGET_USER% to the docker-users group...
net localgroup docker-users "%TARGET_USER%" /add >nul 2>&1
echo [DaranX] Done ^(already a member is fine^).

echo(
echo ============================================================
echo  Docker Desktop is installed.
echo  A RESTART is required. After restarting:
echo    - Docker Desktop starts by itself ^(accept its terms once^)
echo    - then run start.bat, or in this folder:  docker compose up -d
echo(
echo  If Docker complains about virtualization, enable
echo  "Intel VT-x" / "AMD-V" ^(SVM^) in the BIOS/UEFI settings.
echo ============================================================
goto :ask_reboot

:already_installed
echo [DaranX] Docker is already installed.
docker --version 2>nul
net localgroup docker-users "%TARGET_USER%" /add >nul 2>&1
docker info >nul 2>&1
if errorlevel 1 (
    echo [DaranX] Docker engine is not running - starting Docker Desktop...
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else (
    echo [DaranX] Docker engine is running. Nothing to do.
)
goto :end

:ask_reboot
if "%NEED_REBOOT%"=="0" goto :end
echo(
choice /c YN /m "Restart Windows now"
if errorlevel 2 (
    echo [DaranX] OK. Please restart Windows yourself before using Docker.
    goto :end
)
shutdown /r /t 10 /c "DaranX: restarting to finish the Docker installation"
echo [DaranX] Restarting in 10 seconds...

:end
echo(
pause
endlocal
