# Vosk 离线语音模型

这个目录放 Vosk 中文离线模型（`vosk-model-small-cn-0.22`，约 66 MB）。

**模型不进 git** —— 二进制大文件进 git 会让克隆又慢又痛，且不利于评审体验。

需要语音功能时，在仓库根目录运行：

```bash
python3 scripts/download_vosk.py
```

脚本会从官方地址下载并解压到本目录。完成后 `server.py` 会自动加载。

也可以手动下载：<https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip>，
解压到本目录即可。

想换别的 Vosk 模型？设置环境变量 `VOSK_MODEL_PATH` 指向你的模型目录。
