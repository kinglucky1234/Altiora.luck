"""
Altiora 一键自检
    python3 自检.py

检查复现链路上会出问题的地方：依赖、语音模型、前端关键控件、服务能否启动、识别接口是否通。
只查本机，不联网、不调大模型、不消耗 API 额度。

退出码：0 全部通过；1 有 FAIL。
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import wave
from pathlib import Path

BASE = Path(__file__).resolve().parent
HTML = BASE / "Altiora-未来的我.html"
MODEL = BASE / "Altiora" / "backend" / "model" / "vosk-model-small-cn-0.22"

results = []  # (level, name, detail)


def ok(name, detail=""):
    results.append(("PASS", name, detail))


def warn(name, detail=""):
    results.append(("WARN", name, detail))


def fail(name, detail=""):
    results.append(("FAIL", name, detail))


def check_python():
    v = sys.version_info
    if v >= (3, 10):
        ok("Python 版本", f"{v.major}.{v.minor}.{v.micro}")
    else:
        fail("Python 版本", f"{v.major}.{v.minor}，需要 3.10 以上")


def check_deps():
    # 缺依赖是最常见的「装了跑不起来」原因，逐个报名字，别只说 ImportError
    for mod, pkg in [("fastapi", "fastapi"), ("uvicorn", "uvicorn"),
                     ("multipart", "python-multipart"), ("vosk", "vosk")]:
        try:
            __import__(mod)
            ok(f"依赖 {pkg}", "已安装")
        except Exception:
            fail(f"依赖 {pkg}", f"没装。运行：pip install {pkg}")


def check_model():
    must = ["am/final.mdl", "conf/mfcc.conf", "graph/HCLr.fst", "graph/Gr.fst"]
    if not MODEL.is_dir():
        fail("语音模型", f"目录不存在：{MODEL.relative_to(BASE)}。运行 python3 scripts/download_vosk.py 下载")
        return
    missing = [m for m in must if not (MODEL / m).exists()]
    if missing:
        fail("语音模型", "缺文件：" + "、".join(missing))
        return
    size = sum(f.stat().st_size for f in MODEL.rglob("*") if f.is_file()) / 1024 / 1024
    if size < 20:
        warn("语音模型", f"只有 {size:.1f} MB，疑似没下全（完整约 40MB）")
    else:
        ok("语音模型", f"{size:.0f} MB，文件齐全")


def check_frontend():
    if not HTML.exists():
        fail("前端页面", "找不到 Altiora-未来的我.html")
        return
    text = HTML.read_text(encoding="utf-8")
    ids = ["chatIn", "sendBtn", "ttsBtn", "aiPill", "llmMask", "llmHeaders", "kv", "diaryListBox"]
    missing = [i for i in ids if f'id="{i}"' not in text]
    if missing:
        fail("前端控件", "缺：" + "、".join(missing))
    else:
        ok("前端控件", "输入框/发送/朗读/配置面板都在")
    if re.search(r"sk-[A-Za-z0-9]{20,}", text):
        warn("前端页面", "页面里出现了疑似真实 Key 的字符串，检查一下")
    else:
        ok("无硬编码 Key", "页面里没有真实 API Key")


def check_js_syntax():
    """页面里的内联脚本整段跑不起来时，页面看着正常、其实什么都点不动。
    本机有 node 就借它做语法检查；没有就跳过，不误报。"""
    if not HTML.exists():
        return
    node = shutil.which("node")
    if not node:
        warn("前端脚本语法", "本机没有 node，跳过（不影响使用）")
        return
    text = HTML.read_text(encoding="utf-8")
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S)
    bad = []
    for i, code in enumerate(scripts):
        if not code.strip():
            continue
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / f"s{i}.js"
            p.write_text(code, encoding="utf-8")
            r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
            if r.returncode != 0:
                lines = [x.strip() for x in (r.stderr or "").splitlines() if x.strip()]
                hit = next((x for x in lines if "Error:" in x), lines[-1] if lines else "语法错误")
                bad.append(hit)
    if bad:
        fail("前端脚本语法", "；".join(bad)[:300])
    else:
        ok("前端脚本语法", f"{len(scripts)} 段内联脚本语法正常")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def make_wav(path: Path):
    """生成 1 秒 16k 单声道静音 WAV，够验证解码链路。"""
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000)


def post_wav(port: int, wav: Path):
    boundary = "----altiora"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="audio"; filename="t.wav"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
    ).encode() + wav.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/asr", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def check_server():
    port = free_port()
    env = dict(os.environ, PORT=str(port))
    proc = subprocess.Popen(
        [sys.executable, "server.py"], cwd=str(BASE), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    try:
        # 首次加载语音模型可能要十几秒，给足 60 秒
        ready = False
        for _ in range(120):
            if proc.poll() is not None:
                break
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as r:
                    if r.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.5)
        if not ready:
            out = b""
            if proc.poll() is not None:
                out = proc.stdout.read() or b""
            fail("服务启动", "没能起来。" + out.decode(errors="ignore")[-400:].strip())
            return
        ok("服务启动", f"端口 {port} 返回 200")

        wav = BASE / "_selftest.wav"
        make_wav(wav)
        try:
            data = post_wav(port, wav)
            if isinstance(data, dict) and "text" in data:
                ok("识别接口", f"返回 text 字段（静音识别结果 len={len(data.get('text') or '')}）")
            else:
                fail("识别接口", f"返回格式不对：{str(data)[:120]}")
        except Exception as e:
            fail("识别接口", f"{type(e).__name__}: {e}")
        finally:
            wav.unlink(missing_ok=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except Exception:
            proc.kill()


def main():
    print("Altiora 自检\n" + "=" * 48)
    for fn in (check_python, check_deps, check_model, check_frontend,
               check_js_syntax, check_server):
        try:
            fn()
        except Exception as e:
            fail(fn.__name__, f"检查本身出错：{type(e).__name__}: {e}")

    print()
    for level, name, detail in results:
        mark = {"PASS": "[ OK ]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[level]
        print(f"{mark} {name:<12} {detail}")

    n_fail = sum(1 for r in results if r[0] == "FAIL")
    n_warn = sum(1 for r in results if r[0] == "WARN")
    print("=" * 48)
    if n_fail:
        print(f"没通过：{n_fail} 项失败，{n_warn} 项警告。按上面的提示修。")
    elif n_warn:
        print(f"基本可用：{n_warn} 项警告，不影响启动。")
    else:
        print("全部通过。可以运行 python3 server.py 用语音，或直接双击 HTML 用文字。")
    print("\n提醒：语音识别只测了链路（静音 WAV），真实说话效果要你自己对着麦克风说。")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
