#!/usr/bin/env bash
# Altiora 一键启动（macOS / Linux）
cd "$(dirname "$0")" || exit 1

PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "没找到 python3，请先安装 Python 3.10+。"
  exit 1
fi

if ! "$PY" -c "import fastapi,uvicorn,vosk,multipart" >/dev/null 2>&1; then
  echo "第一次运行，正在安装依赖..."
  "$PY" -m pip install -r requirements.txt || exit 1
fi

(
  sleep 2
  if command -v open >/dev/null 2>&1; then open "http://localhost:8000"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:8000"
  fi
) &

exec "$PY" server.py
