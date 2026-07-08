@echo off
REM AgentBuddy 完整构建脚本（前端 + 后端 + PyInstaller 打包）
REM 用法: build.cmd [--windowed] [--clean] [--no-frontend] [--no-verify]
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo [build] AgentBuddy 完整构建

REM ===== 1. 前端构建 =====
if not exist "frontend\node_modules" (
    echo [build] 安装前端依赖...
    cd frontend && npm install && cd ..
)
echo [build] 步骤 1/4: 构建前端 (Vue 3 + Vite)...
cd frontend
call npm run build-only
if errorlevel 1 (
    echo [build][ERROR] 前端构建失败
    exit /b 1
)
cd ..
echo [build] 前端产物: tools\dist-ui\

REM ===== 2. Python 依赖 =====
echo [build] 步骤 2/4: 检查 Python 依赖...
python -c "import flask, yaml, requests" 2>nul
if errorlevel 1 (
    echo [build] 安装运行时依赖...
    python -m pip install flask pyyaml requests pywebview
)
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [build] 安装 PyInstaller...
    python -m pip install pyinstaller
)

REM ===== 3. PyInstaller 打包 =====
echo [build] 步骤 3/4: PyInstaller 打包...
python build.py %*
if errorlevel 1 (
    echo [build][ERROR] PyInstaller 打包失败
    exit /b 1
)

REM ===== 4. 验证前端产物 =====
echo [build] 步骤 4/4: 验证前端产物...
if exist "dist\AgentBuddy\_internal\tools\dist-ui\index.html" (
    echo [build] 前端产物已进 bundle
) else if exist "dist\AgentBuddy\tools\dist-ui\index.html" (
    echo [build] 前端产物已进 bundle
) else (
    echo [build][WARN] 前端产物未在 bundle 中找到
)

echo.
echo [build] ========================================
echo [build]   构建完成！
echo [build] ========================================
echo [build]   产物目录: dist\AgentBuddy\
echo [build]   启动:     dist\AgentBuddy\AgentBuddy.exe
echo.
endlocal
