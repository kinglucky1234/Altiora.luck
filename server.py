"""
Altiora 本地服务
- 打开网页
- 离线语音识别（Vosk，纯本地，不需要 API Key，也不需要联网）

用法：python3 server.py
然后浏览器打开 http://localhost:8000
"""
import json
import os
import subprocess
import tempfile
import wave
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

BASE = Path(__file__).resolve().parent
MODEL_DIR = Path(
    os.environ.get("VOSK_MODEL_PATH")
    or BASE / "Altiora" / "backend" / "model" / "vosk-model-small-cn-0.22"
)
PORT = int(os.environ.get("PORT", "8000"))
HTML = BASE / "Altiora-未来的我.html"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_model = None


def get_model():
    global _model
    if _model is None:
        from vosk import Model, SetLogLevel
        SetLogLevel(-1)
        _model = Model(str(MODEL_DIR))
    return _model


@app.get("/")
def index():
    return FileResponse(HTML, media_type="text/html; charset=utf-8")


@app.get("/{name}")
def page(name: str):
    if name.endswith(".html"):
        return FileResponse(HTML, media_type="text/html; charset=utf-8")
    return JSONResponse({"error": "not found"}, status_code=404)


@app.post("/api/asr")
async def asr(audio: UploadFile = File(...)):
    """浏览器录音（webm/ogg/wav）→ 文字。"""
    raw = await audio.read()
    if not raw:
        return {"text": ""}
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.bin")
        wav = os.path.join(td, "out.wav")
        with open(src, "wb") as f:
            f.write(raw)
        subprocess.run(
            ["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", "-f", "wav", wav],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if not os.path.exists(wav):
            return JSONResponse({"text": "", "error": "audio decode failed"})

        from vosk import KaldiRecognizer
        with wave.open(wav, "rb") as wf:
            rec = KaldiRecognizer(get_model(), wf.getframerate())
            parts = []
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                if rec.AcceptWaveform(data):
                    parts.append(json.loads(rec.Result()).get("text", ""))
            parts.append(json.loads(rec.FinalResult()).get("text", ""))

    text = "".join(parts).replace(" ", "")
    return {"text": text}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
