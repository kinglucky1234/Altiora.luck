"""
Altiora 本地服务
- 打开网页
- 离线语音识别（Vosk，纯本地，不需要 API Key，也不需要联网）

用法：python3 server.py
然后浏览器打开 http://localhost:8000
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

BASE = Path(__file__).resolve().parent


def _load_dotenv():
    """读 .env（不引入额外依赖）。已存在的环境变量优先。"""
    for p in (BASE / ".env", BASE.parent / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

BACKEND = BASE / "Altiora" / "backend"
sys.path.insert(0, str(BACKEND))
import llm  # noqa: E402  —— AI 翻译官（未配 Key 时自动退回规则）

MODEL_DIR = Path(
    os.environ.get("VOSK_MODEL_PATH")
    or BACKEND / "model" / "vosk-model-small-cn-0.22"
)
PORT = int(os.environ.get("PORT", "8000"))
HTML = BASE / "Altiora-未来的我.html"


@asynccontextmanager
async def lifespan(_app):
    """启动时先把语音模型读进内存，第一次说话不用再等几秒。"""
    if MODEL_DIR.is_dir():
        try:
            get_model()
        except Exception:
            pass
    yield


app = FastAPI(lifespan=lifespan)
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


@app.get("/api/health")
def health():
    """给前端显示用：LLM 是否在线、语音模型是否就位。"""
    return {
        "ok": True,
        "llm": llm.enabled(),
        "model": llm.model_name() if llm.enabled() else None,
        "asr": MODEL_DIR.is_dir(),
    }


@app.post("/api/understand")
async def understand(req: dict = Body(...)):
    """
    AI 翻译官：自然语言 → 结构化字段。
    只做理解，不做任何计算；失败时返回 ok=False，前端退回本地规则。
    """
    text = str(req.get("text") or "").strip()
    if not text:
        return {"ok": False, "source": "rule", "reason": "empty"}
    return llm.understand(
        text,
        req.get("profile") or {},
        key=req.get("api_key"),
        base=req.get("base_url"),
        model=req.get("model"),
        headers=req.get("headers"),
    )


@app.post("/api/say")
async def say(req: dict = Body(...)):
    """
    第二段翻译官：计算器算出的确定结果 → 一句人话。
    模型只能引用给定数字，写错就作废，前端退回模板。
    """
    facts = req.get("facts")
    if not isinstance(facts, dict) or not facts:
        return {"ok": False, "reason": "empty_facts"}
    return llm.say(
        facts,
        req.get("profile") or {},
        key=req.get("api_key"),
        base=req.get("base_url"),
        model=req.get("model"),
        headers=req.get("headers"),
    )


@app.post("/api/asr")
async def asr(audio: UploadFile = File(...)):
    """浏览器录音（webm/ogg/wav）→ 文字。"""
    raw = await audio.read()
    if not raw:
        return {"text": ""}
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "out.wav")
        if raw[:4] == b"RIFF" and raw[8:12] == b"WAVE":
            # 浏览器直接录好的 16k 单声道 WAV，不用转码，也就不需要 ffmpeg
            with open(wav, "wb") as f:
                f.write(raw)
        else:
            src = os.path.join(td, "in.bin")
            with open(src, "wb") as f:
                f.write(raw)
            if not shutil.which("ffmpeg"):
                return {"text": "", "error": "ffmpeg not found"}
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
