@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   FusionFlows Windows Standalone Builder (CPU Edition)
echo ========================================================
echo.

:: Check Python
py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py -3.12
    goto :python_found
)

py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py -3.11
    goto :python_found
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :python_found
)

echo [ERROR] Python 3.11 or 3.12 was not found. Please install Python 3.12 and try again.
pause
exit /b 1

:python_found
echo [INFO] Using Python: %PY_CMD%

:: Create Virtual Environment
if not exist .venv (
    echo [INFO] Creating virtual environment (.venv)...
    %PY_CMD% -m venv .venv
)

:: Activate Virtual Environment
call .venv\Scripts\activate.bat

:: Upgrade Pip & Install Dependencies
echo [INFO] Installing required dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

:: Check bundled ffmpeg
if not exist bin\ffmpeg.exe (
    echo [INFO] Copying ffmpeg binaries to bin folder...
    mkdir bin 2>nul
    where ffmpeg >nul 2>&1 && (
        for /f "tokens=*" %%i in ('where ffmpeg') do copy /y "%%i" bin\ffmpeg.exe >nul
    )
    where ffprobe >nul 2>&1 && (
        for /f "tokens=*" %%i in ('where ffprobe') do copy /y "%%i" bin\ffprobe.exe >nul
    )
)

:: Run PyInstaller
echo [INFO] Packaging FusionFlows.exe...
pyinstaller FusionFlows.spec

echo.
echo ========================================================
echo   Build complete! Output: dist\FusionFlows.exe
echo ========================================================
pause
