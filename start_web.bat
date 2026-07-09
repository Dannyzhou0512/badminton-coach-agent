@echo off
chcp 65001 >nul
title 羽动智练 - Web 启动器

cd /d "%~dp0"

echo ============================================
echo   羽动智练 Badminton AI Coach
echo ============================================
echo.

echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到 Python。
    echo 请安装 Python 3.10 或更高版本，并勾选 Add Python to PATH。
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python 版本: %PYVER%
echo.

echo [2/5] 检查依赖包...
python -c "import fastapi, uvicorn, cv2, torch, ultralytics" >nul 2>&1
if errorlevel 1 (
    echo 检测到缺少依赖，正在安装 requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo 依赖检查完成。
echo.

echo [3/5] 检查模型文件...
if not exist "yolov8s-pose.pt" (
    echo 未找到 yolov8s-pose.pt，正在尝试自动下载...
    python -c "from ultralytics import YOLO; YOLO('yolov8s-pose.pt')"
)
if not exist "models\pose_sequence_tcn_gru.pt" (
    echo 错误: 未找到动作分类模型 models\pose_sequence_tcn_gru.pt
    echo 请确认模型文件已放置到 models 目录。
    pause
    exit /b 1
)
echo 模型检查完成。
echo.

echo [4/5] 检查 FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo 提示: 未检测到 FFmpeg，标注视频生成速度可能较慢。
    echo 建议安装 FFmpeg 并加入系统 PATH: https://www.gyan.dev/ffmpeg/builds/
) else (
    echo FFmpeg 可用。
)
echo.

echo [5/5] 检查 GPU...
python -c "import torch; assert torch.cuda.is_available()" >nul 2>&1
if errorlevel 1 (
    echo 未检测到 NVIDIA CUDA GPU，将使用 CPU 模式。
) else (
    for /f "tokens=* delims=" %%g in ('python -c "import torch; print(torch.cuda.get_device_name(0))"') do set GPU=%%g
    echo GPU 加速可用: %GPU%
)
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do (
    for /f "tokens=1 delims= " %%b in ("%%a") do set LAN_IP=%%b
)

echo ============================================
echo   正在启动服务
echo ============================================
echo 本机访问: http://127.0.0.1:8000/frontend/
if defined LAN_IP (
    echo 局域网访问: http://%LAN_IP%:8000/frontend/
    echo 小程序 API_BASE 可配置为: http://%LAN_IP%:8000
)
echo 关闭本窗口即可停止服务。
echo.

start "" "http://127.0.0.1:8000/frontend/"
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

echo.
echo 服务已停止。
pause
