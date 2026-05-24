@echo off
title Game Collection Builder

echo ====================================
echo   Game Collection - Windows Builder
echo ====================================
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Install from https://www.python.org/downloads/
    echo        Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo [OK] Python:
python --version

:: Check / Install PyInstaller
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [..] Installing PyInstaller...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] PyInstaller install failed
        pause
        exit /b 1
    )
) else (
    echo [OK] PyInstaller ready
)

echo.
echo [..] Building executable (this may take a while)...
echo.

pyinstaller build.spec
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed - see errors above
    pause
    exit /b 1
)

echo.
echo ========== SUCCESS ==========
echo.
echo Output:
echo    %CD%\dist\GameCollection.exe
echo.
echo Double-click to run, no Python needed.
echo.
pause
