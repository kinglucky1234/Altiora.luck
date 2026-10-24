@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo   Altiora . 配置大模型
echo ============================================
echo.
echo   1  DeepSeek（便宜，推荐）
echo   2  通义千问（阿里云百炼）
echo   3  火山方舟（豆包模型）
echo   4  其他 OpenAI 兼容接口
echo.
set /p CH=请输入序号（直接回车 = 1）:
if "%CH%"=="" set "CH=1"

set "BASE=https://api.deepseek.com/v1"
set "MODEL=deepseek-chat"
if "%CH%"=="2" set "BASE=https://dashscope.aliyuncs.com/compatible-mode/v1"
if "%CH%"=="2" set "MODEL=qwen-plus"
if "%CH%"=="3" set "BASE=https://ark.cn-beijing.volces.com/api/v3"
if "%CH%"=="3" set "MODEL="
if "%CH%"=="4" set "BASE="
if "%CH%"=="4" set "MODEL="

if "%CH%"=="3" set /p MODEL=请粘贴方舟的接入点 ID（形如 ep-2024xxxx）:
if "%CH%"=="4" set /p BASE=请粘贴 Base URL（到 /v1 为止）:
if "%CH%"=="4" set /p MODEL=请粘贴模型名:

echo.
set /p KEY=请粘贴 API Key，然后回车:
if "%KEY%"=="" (
  echo 没填 Key，已取消。
  pause
  exit /b 1
)

> .env echo PORT=8000
>> .env echo VOSK_MODEL_PATH=
>> .env echo LLM_API_KEY=%KEY%
>> .env echo LLM_BASE_URL=%BASE%
>> .env echo LLM_MODEL=%MODEL%

echo.
echo 完成：配置已写入 .env（这个文件不会上传到 GitHub）。
echo 现在关掉正在运行的黑窗口，重新双击「启动.bat」。
echo 页面右上角变成「AI 在线」，就说明接上了。
echo.
pause
