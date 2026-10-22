#!/bin/bash
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[x] 没装 Python 3。"
  echo "    去 https://www.python.org/downloads/ 下载安装"
  read -n 1 -s -r -p "按任意键退出..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[i] 第一次跑，正在准备环境（可能要几分钟）..."
  python3 -m venv .venv
  . .venv/bin/activate
  python3 -m pip install --upgrade pip -q
  pip install -r requirements.txt -q
  echo "[✓] 环境装好啦"
else
  . .venv/bin/activate
fi

echo "[i] 正在启动，浏览器会自动打开 http://localhost:8000"
open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null &
python3 server.py
read -n 1 -s -r -p "按任意键退出..."
