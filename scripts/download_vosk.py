#!/usr/bin/env python3
"""下载 Vosk 中文离线语音识别模型。

模型体积约 66 MB，不放进 git（克隆会又慢又痛）。需要语音功能时运行本脚本一次即可。

用法：
    python3 scripts/download_vosk.py

下载后模型落在 Altiora/backend/model/vosk-model-small-cn-0.22/，
server.py 会自动从该目录加载。若想换别的模型，设置环境变量 VOSK_MODEL_PATH。
"""
import os
import sys
import zipfile
import urllib.request

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"
MODEL_NAME = "vosk-model-small-cn-0.22"

# 脚本在 scripts/ 下，模型目录在 ../Altiora/backend/model/
TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "Altiora", "backend", "model")


def main() -> int:
    target = os.path.abspath(TARGET_DIR)
    os.makedirs(target, exist_ok=True)
    model_path = os.path.join(target, MODEL_NAME)

    if os.path.isdir(model_path):
        print(f"模型已存在，跳过：{model_path}")
        return 0

    zip_path = os.path.join(target, f"{MODEL_NAME}.zip")
    print(f"下载 {MODEL_URL}")
    print(f"  -> {zip_path}")
    try:
        urllib.request.urlretrieve(MODEL_URL, zip_path)
    except Exception as e:
        print(f"下载失败：{e}", file=sys.stderr)
        print("可手动从上述地址下载 zip，解压到：", target, file=sys.stderr)
        return 1

    print(f"解压到 {target} ...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(target)
    os.remove(zip_path)
    print(f"完成：{model_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
