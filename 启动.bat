@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo   Altiora 启动中...
echo.

rem ── 找 Python ──
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo   没找到 Python。
  echo   请先安装 Python 3.10 以上版本，安装第一步记得勾选 "Add Python to PATH"。
  echo   下载地址：https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

rem ── 第一次运行自动装依赖 ──
%PY% -c "import fastapi,uvicorn,vosk,multipart" >nul 2>nul
if errorlevel 1 (
  echo   第一次运行，正在安装依赖，大概 1-2 分钟...
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo   依赖安装失败。检查一下网络，或者手动运行：pip install -r requirements.txt
    pause
    exit /b 1
  )
)

rem ── 确认语音模型在 ──
if not exist "Altiora\backend\model\vosk-model-small-cn-0.22\am" (
  echo   提示：没找到语音模型目录，文字聊天不受影响，语音会不可用。
)

echo   正在打开 http://localhost:8000
echo   这个黑窗口不要关，关掉服务就停了。
echo.
start "" cmd /c "timeout /t 2 >nul & start http://localhost:8000"

%PY% server.py

echo.
echo   服务已停止。
pause
