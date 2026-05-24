@echo off
chcp 65001 >nul
title 打包游戏合集

echo ====================================
echo   🎮 游戏合集 - Windows 打包工具
echo ====================================
echo.

:: 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python，请先安装 https://www.python.org/downloads/
    echo    安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python: 
python --version

:: 检查 / 安装 PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 正在安装 PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ❌ PyInstaller 安装失败
        pause
        exit /b 1
    )
) else (
    echo ✅ PyInstaller 已安装
)

echo.
echo 🔨 正在打包，请稍候...
echo.

:: 执行打包
pyinstaller build.spec

if %errorlevel% neq 0 (
    echo ❌ 打包失败，请检查上面的错误信息
    pause
    exit /b 1
)

echo.
echo ✅ 打包成功！
echo.
echo 📁 可执行文件位置：
echo    %CD%\dist\游戏合集.exe
echo.
echo 🚀 双击即可运行，无需安装 Python
echo.
pause
