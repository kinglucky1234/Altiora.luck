@echo off
chcp 65001 >nul
title Altiora · 未来的你
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo [x] 没装 Python。
  echo     去 https://www.python.org/downloads/ 下载安装，安装时勾上 "Add Python to PATH"
  echo.
  pause
  exit /b
)

if not exist ".venv" (
  echo [i] 第一次跑，正在准备环境（可能要几分钟）...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip -q
  pip install -r requirements.txt -q
  echo [✓] 环境装好啦
) else (
  call .venv\Scripts\activate.bat
)

echo [i] 正在启动，浏览器会自动打开 http://localhost:8000
start "" http://localhost:8000
python server.py
pause
