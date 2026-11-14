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
import threading
import wave
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI, Request, UploadFile, File, Response
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
            v = v.strip()
            # 去掉行内注释："50      # 说明" → "50"
            # 只在 # 前面是空白时才当注释，避免误伤值里合法的 # 字符
            for sep in (" #", "\t#"):
                if sep in v:
                    v = v.split(sep, 1)[0]
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

BACKEND = BASE / "backend"
sys.path.insert(0, str(BACKEND))
import llm  # noqa: E402  —— AI 翻译官（未配 Key 时自动退回规则）

MODEL_DIR = Path(
    os.environ.get("VOSK_MODEL_PATH")
    or BACKEND / "model" / "vosk-model-small-cn-0.22"
)
PORT = int(os.environ.get("PORT", "8000"))
HTML = BASE / "Altiora-未来的我.html"

# ── 限流：防止服务器上的免费 Key 被刷爆 ──────────────────────────
# 只对调大模型的两个接口（/api/understand、/api/say）生效；
# /api/asr 是本地语音，不花 Key 钱，不限。
RATE_PER_IP_DAY = int(os.environ.get("RATE_PER_IP_DAY", "50"))   # 每个 IP 每天最多调多少次大模型
RATE_GLOBAL_DAY = int(os.environ.get("RATE_GLOBAL_DAY", "1000"))  # 全服务器每天总上限
_rate_lock = threading.Lock()
_rate = {"day": "", "ip": {}, "total": 0}


def _client_ip(request: Request) -> str:
    """取真实客户端 IP：优先 X-Forwarded-For（反代/隧道后），再退到直连 IP。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate(request: Request):
    """每日（按服务器本地日期）重置计数器；超限返回 429，否则返回 None。"""
    today = date.today().isoformat()
    ip = _client_ip(request)
    with _rate_lock:
        if _rate["day"] != today:
            _rate["day"] = today
            _rate["ip"] = {}
            _rate["total"] = 0
        if _rate["total"] >= RATE_GLOBAL_DAY:
            return JSONResponse({"ok": False, "error": "rate_limit", "reason": "global_daily"}, status_code=429)
        used = _rate["ip"].get(ip, 0)
        if used >= RATE_PER_IP_DAY:
            return JSONResponse({"ok": False, "error": "rate_limit", "reason": "ip_daily"}, status_code=429)
        _rate["ip"][ip] = used + 1
        _rate["total"] += 1
        return None


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


def _asr_available() -> bool:
    """完整检查：vosk 包能导入 + 模型目录存在 + 模型能加载。"""
    if not MODEL_DIR.is_dir():
        return False
    try:
        import vosk  # noqa: F401
    except ImportError:
        return False
    try:
        get_model()
        return True
    except Exception:
        return False


def get_model():
    global _model
    if _model is None:
        try:
            from vosk import Model, SetLogLevel
        except ImportError as e:
            raise RuntimeError(f"vosk 未安装: {e}") from e
        SetLogLevel(-1)
        _model = Model(str(MODEL_DIR))
    return _model


@app.get("/")
def index():
    return FileResponse(HTML, media_type="text/html; charset=utf-8")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """浏览器默认会来要图标。返回 204，控制台别留一条红字 404。"""
    return Response(status_code=204)


@app.get("/{name}")
def page(name: str):
    """只暴露仓库根目录下的 .html 文件，防路径穿越；不存在返回 404。

    之前任何 .html 都返回主页面，avatar-preview.html / Altiora-给老师看.html
    在服务模式下其实是假路由。现在按文件名真实返回。
    """
    if not name.endswith(".html"):
        return JSONResponse({"error": "not found"}, status_code=404)
    base = str(BASE.resolve())
    target = str((BASE / name).resolve())
    # 防路径穿越：target 必须落在 BASE 内（用 commonpath，兼容 3.10）
    if os.path.commonpath([base, target]) != base or target == base:
        return JSONResponse({"error": "not found"}, status_code=404)
    if not os.path.isfile(target):
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(target, media_type="text/html; charset=utf-8")


@app.get("/api/health")
def health():
    """给前端显示用：LLM 是否在线、语音模型是否就位。"""
    return {
        "ok": True,
        "llm": llm.enabled(),
        "model": llm.model_name() if llm.enabled() else None,
        "asr": _asr_available(),
    }


@app.post("/api/understand")
async def understand(request: Request, req: dict = Body(...)):
    """
    AI 翻译官：自然语言 → 结构化字段。
    只做理解，不做任何计算；失败时返回 ok=False，前端退回本地规则。
    """
    limited = _check_rate(request)
    if limited is not None:
        return limited
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
        history=req.get("history"),
    )


@app.post("/api/say")
async def say(request: Request, req: dict = Body(...)):
    """
    第二段翻译官：计算器算出的确定结果 → 一句人话。
    模型只能引用给定数字，写错就作废，前端退回模板。
    """
    limited = _check_rate(request)
    if limited is not None:
        return limited
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
    """浏览器录音（webm/ogg/wav）→ 文字。

    降级策略：vosk 包没装 / 模型目录不存在 / 模型损坏 → 返回空文本，
    但不崩溃。前端看到空文本会提示用户，页面继续能用（只是没语音）。
    """
    raw = await audio.read()
    if not raw:
        return {"text": ""}

    # ① vsk 整体不可用 → 直接降级
    if not _asr_available():
        return {"text": "", "degraded": True, "hint": "语音模型未就绪，请用文字输入"}

    try:
        with tempfile.TemporaryDirectory() as td:
            wav = os.path.join(td, "out.wav")
            if raw[:4] == b"RIFF" and raw[8:12] == b"WAVE":
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
    except Exception:
        # 模型跑起来了但识别中间炸了（音频格式不对、内存不足等）
        # 统一降级：返回空文本，不崩溃
        return {"text": "", "degraded": True, "hint": "识别出错，请再说一次或用文字"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
