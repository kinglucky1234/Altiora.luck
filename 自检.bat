@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
python 自检.py
echo.
pause
