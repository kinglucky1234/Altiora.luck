"""
AI 翻译官（LLM 版）

只做两件事：
  1. 理解：自然语言 → 结构化字段（意图 / 事件 / 记忆 / 目标 / 情绪）
  2. 表达：情绪与闲聊场景 → 一句人话

明确不做：
  - 不判断冲突、不算重叠分钟、不算时长、不算钱（那是计算器的事）
  - 不替用户做选择
  - 不补全用户没说的信息（没说时间就不编时间）
  - 不在 schedule / memory / goal / safety 场景生成回复

没配 Key 或调用失败时返回 ok=False，前端自动退回本地规则 —— 离线也能完整跑。
"""
from __future__ import annotations  # PEP 563：延迟求值注解，让 str | None / list[dict] 在 3.8+ 也能跑

import ipaddress
import json
import os
import re
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

TIMEOUT = 12
MAX_INPUT = 600

INTENTS = {"safety", "emotion", "schedule", "memory", "goal", "chat"}
EMOTIONS = {"sad", "tired", "anxious", "selfblame", "relapse", "lonely", "numb", "none"}

# 万金油句式：模型一旦写出这些，服务端直接作废，让前端用自己的话兜底
_BANNED = re.compile(
    r"嗯[，,]\s*我在听|我在听|你接着说|我在这儿|我都在|会好起来的|会好一点|"
    r"加油|你可以的|相信自己|慢慢来|不要放弃|你能做到"
)
_NUM = re.compile(r"\d+(?:\.\d+)?")

SYSTEM = """你叫 Altiora，是「用户理想中更好的自己」在电脑里的投影，不是客服，也不是心理医生。

你的职责只有翻译，不做决策。

【判断 intent，只能选一个】
- safety：出现不想活、自伤、结束生命的意味
- emotion：在倾诉情绪、状态、自我否定
- schedule：明确说出一件带开始与结束时间的事，要排进日程
- memory：明确要求记住一条规矩或软肋（如「记住…」「以后不…」）
- goal：说出长期目标
- chat：其它闲聊

【抽取规则】
- event 只在 intent=schedule 时给，且必须同时有 start 和 end（24 小时制 HH:MM）。
  用户没说结束时间，event 就填 null，不要猜。
- memory 只在用户明确要求记住时给，text 原样保留用户的话，不要改写。
- goal 只保留目标本身，去掉「我想」这类前缀。

【绝对不能做】
- 不计算时间重叠、时长、金钱、代价
- 不替用户选方案，不说「你应该选 A」
- 不编造用户没说的地点、时间、人物
- 不说「加油」「你可以的」「相信自己」，不喊口号，不做心理诊断
- 不复述用户原话，不用客服腔

【reply 的写法（这一栏最容易被写成客服腔，逐条遵守）】
- intent=safety：null（前端有固定安全话术）
- intent=schedule 且 event 完整（有 start 和 end）：null。账要由计算器算完再回来说，你不能抢答。
- 其它情况一律要写，一到两句，40 字以内。
- 必须指涉用户刚说的具体内容：那件事的名字、那个时间、那个词。只写放之四海皆准的话等于没听懂。
- 禁止出现这些句式（及同类）：嗯，我在听 / 你接着说 / 我在这儿 / 说出来会好一点 / 会好起来的 / 加油 / 你可以的 / 相信自己 / 慢慢来。
- 不确定就问一个具体问题（二选一，或要一个时间），不要问「你还好吗」这种空问题。
- 情绪：先接住，不分析、不劝、不给方案；可以承认「今天就这样也行」。
- 闲聊：正常聊天，可以有一点幽默，但别硬逗。

只输出 JSON，不要解释，不要 Markdown 代码块：
{"intent":"emotion","emotion":"tired","event":null,"memory":null,"goal":null,"reply":"..."}"""

SAY_SYSTEM = """你是 Altiora，用户理想中更好的自己在电脑里的投影。下面是本地计算器算出的确定结果，你只负责把它说成一句人话。

规则：
- 只能引用给定数字，一个都不许改、不许加、不许四舍五入、不许推算新数字
- 不替用户选择，不给建议，不评价对错
- 一到两句，50 字以内
- 语气平静、具体，说清发生了什么（哪两件事撞了、撞了多久）
- 禁止「加油」「你可以的」「相信自己」「嗯，我在听」这类句子
- 只说结果，不要重复用户原话

只输出那一句话，不要引号，不要解释，不要 Markdown。"""


def _api_key() -> str:
    return os.environ.get("LLM_API_KEY", "").strip()


def _base_url() -> str:
    return (os.environ.get("LLM_BASE_URL", "").strip() or "https://api.openai.com/v1").rstrip("/")


def model_name() -> str:
    return os.environ.get("LLM_MODEL", "").strip() or "gpt-4o-mini"


def enabled() -> bool:
    return bool(_api_key())


def _resolve(key: str | None, base: str | None, model: str | None):
    """用户自己带来的 Key 优先，其次才是服务器 .env。"""
    k = (key or _api_key()).strip()
    b = ((base or os.environ.get("LLM_BASE_URL", "")).strip() or "https://api.openai.com/v1").rstrip("/")
    m = (model or model_name()).strip()
    return k, b, m


_PRIVATE_HOSTS = ("localhost", "127.", "10.", "192.168.", "169.254.", "0.")


_HEADER_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_BLOCKED_HEADERS = {"host", "content-length", "connection", "transfer-encoding"}


def _merge_headers(base_headers: dict, extra) -> dict:
    """合上用户自填的额外请求头（中转站常用）。只做最小校验，防止头注入。"""
    if not isinstance(extra, dict):
        return base_headers
    for k, v in list(extra.items())[:20]:
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        k, v = k.strip(), v.strip()
        if not _HEADER_NAME.match(k) or k.lower() in _BLOCKED_HEADERS:
            continue
        if len(v) > 1024 or "\r" in v or "\n" in v:
            continue
        base_headers[k] = v
    return base_headers


def _is_private_ip(ip_str: str) -> bool:
    """判断一个 IP 是否属于内网/回环/保留等不应被外部请求打到的范围。"""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # 不是合法 IP，直接拒绝
    # 回环 / 私网(RFC1918+CGNAT) / 链路本地 / 保留 / 组播 / 未指定 一律拒绝
    return (ip.is_loopback or ip.is_private or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def _safe_base(base: str) -> bool:
    """用户自填的地址只允许公网 https，避免被当成内网探针。

    两层防护：
    1. 主机名字符串前缀过滤（快速挡掉 localhost、127.x 等明显内网）
    2. DNS 解析后逐一检查返回的 IP，防 DNS 重绑定（域名解析到内网 IP）

    注意：不防 TOCTOU（解析后到真正请求之间 DNS 再次变化），比赛场景足够。
    """
    u = urlparse(base)
    if u.scheme != "https" or not u.hostname:
        return False
    h = u.hostname.lower()
    # 第一层：字符串前缀快速过滤
    if h == "::1" or any(h == p or h.startswith(p) for p in _PRIVATE_HOSTS):
        return False
    if h.startswith("172."):
        try:
            if 16 <= int(h.split(".")[1]) <= 31:
                return False
        except (IndexError, ValueError):
            return False
    # 第二层：DNS 解析，防 DNS 重绑定
    try:
        infos = socket.getaddrinfo(h, u.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False  # 解析失败也拒绝，不冒险
    for info in infos:
        if _is_private_ip(info[4][0]):
            return False
    return True


# ─── 结构化输出校验（边界处只做格式校验，不做任何计算） ───
_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _norm_time(v) -> str | None:
    if not isinstance(v, str):
        return None
    m = _TIME_RE.match(v.strip().replace("：", ":"))
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def _to_minutes(hm: str) -> int:
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def _clean_event(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name") or "").strip()[:20]
    start = _norm_time(raw.get("start"))
    end = _norm_time(raw.get("end"))
    if not name or not start or not end:
        return None
    # 只校验区间合法，不做任何时长/代价推导
    if _to_minutes(end) <= _to_minutes(start):
        return None
    return {
        "name": name,
        "start": start,
        "end": end,
        "loc": str(raw.get("loc") or "").strip()[:20],
    }


def _clean_memory(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    text = str(raw.get("text") or "").strip()[:60]
    if not text:
        return None
    kind = raw.get("kind")
    return {"kind": kind if kind in ("rule", "weakness") else "rule", "text": text}


def _parse_json(content: str) -> dict | None:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", content).strip()
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        l, r = content.find("{"), content.rfind("}")
        if l < 0 or r <= l:
            return None
        try:
            obj = json.loads(content[l:r + 1])
        except json.JSONDecodeError:
            return None
    return obj if isinstance(obj, dict) else None


def _chat(messages: list[dict], api_key: str, base: str, model: str,
          extra_headers=None) -> str:
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 400,
    }).encode("utf-8")
    headers = _merge_headers({
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }, extra_headers)
    req = urllib.request.Request(
        base + "/chat/completions",
        data=body,
        method="POST",
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def _profile_brief(profile: dict) -> str:
    if not isinstance(profile, dict):
        return "（无）"
    lines = []
    if profile.get("hard_sleep_deadline"):
        lines.append(f"- 睡觉硬约束：{profile['hard_sleep_deadline']} 前")
    if profile.get("long_term_goal"):
        lines.append(f"- 长期目标：{profile['long_term_goal']}")
    weak = profile.get("known_weakness")
    if isinstance(weak, list) and weak:
        lines.append("- 已知软肋：" + "、".join(str(w) for w in weak[:5]))
    return "\n".join(lines) or "（无）"


def understand(text: str, profile: dict | None = None,
               key: str | None = None, base: str | None = None,
               model: str | None = None, headers=None,
               history: list | None = None) -> dict:
    """自然语言 → 结构化字段。失败一律返回 ok=False，由前端兜底。

    key/base/model/headers 由调用方传入时优先使用（用户自带 Key 模式），
    服务器不保存、不记录这些值。
    """
    text = (text or "").strip()
    if not text:
        return {"ok": False, "source": "rule", "reason": "empty"}

    api_key, base_url, model_id = _resolve(key, base, model)
    if not api_key:
        return {"ok": False, "source": "rule", "reason": "no_api_key"}
    if key and not _safe_base(base_url):
        return {"ok": False, "source": "rule", "reason": "unsafe_base"}

    user = (
        "用户画像（已知事实，不要重复询问，也不要复述）：\n"
        f"{_profile_brief(profile or {})}\n\n"
        f"用户刚刚说：{text[:MAX_INPUT]}"
    )

    try:
        # 聊天记忆只带最近 3 轮，够接住「就那个」「三点」这种半句，不堆历史
        msgs = [{"role": "system", "content": SYSTEM}]
        for h in (history or [])[-6:]:
            if not isinstance(h, dict):
                continue
            role = "assistant" if str(h.get("role")) == "assistant" else "user"
            content = str(h.get("text") or "").strip()[:120]
            if content:
                msgs.append({"role": role, "content": content})
        msgs.append({"role": "user", "content": user})
        content = _chat(msgs, api_key, base_url, model_id, headers)
    except urllib.error.HTTPError as e:
        return {"ok": False, "source": "rule", "reason": f"http_{e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"ok": False, "source": "rule", "reason": "network"}
    except Exception:
        return {"ok": False, "source": "rule", "reason": "unknown"}

    obj = _parse_json(content)
    if not obj:
        return {"ok": False, "source": "rule", "reason": "bad_json"}

    intent = obj.get("intent")
    if intent not in INTENTS:
        return {"ok": False, "source": "rule", "reason": "bad_intent"}

    emotion = obj.get("emotion")
    if emotion not in EMOTIONS:
        emotion = "none"

    event = _clean_event(obj.get("event")) if intent == "schedule" else None
    # 时间不全时仍保留主题，前端会追问时间，而不是替用户编一个
    subject = None
    if intent == "schedule" and isinstance(obj.get("event"), dict):
        subject = str(obj["event"].get("name") or "").strip()[:20] or None
    memory = _clean_memory(obj.get("memory")) if intent == "memory" else None
    goal = str(obj.get("goal") or "").strip()[:60] or None if intent == "goal" else None

    reply = obj.get("reply")
    reply = str(reply).strip()[:120] if isinstance(reply, str) else None
    # 服务端硬约束：完整日程不给话术（账还没算），安全一律本地处理
    if intent in ("safety",) or (intent == "schedule" and event):
        reply = None
    if reply and _BANNED.search(reply):
        reply = None

    return {
        "ok": True,
        "source": "llm",
        "intent": intent,
        "emotion": emotion,
        "event": event,
        "subject": subject,
        "memory": memory,
        "goal": goal,
        "reply": reply,
        "model": model_id,
    }


def _numbers(s) -> set:
    return set(_NUM.findall(str(s)))


def say(facts: dict, profile: dict | None = None,
        key: str | None = None, base: str | None = None,
        model: str | None = None, headers=None) -> dict:
    """第二段翻译官：计算器的确定结果 → 一句人话。

    只允许引用 facts 里已有的数字，写错一个数字就整句作废（返回 ok=False）。
    """
    api_key, base_url, model_id = _resolve(key, base, model)
    if not api_key:
        return {"ok": False, "reason": "no_api_key"}
    if key and not _safe_base(base_url):
        return {"ok": False, "reason": "unsafe_base"}

    fact_json = json.dumps(facts, ensure_ascii=False)
    user = (
        f"用户画像（仅供语气参考，不要复述）：\n{_profile_brief(profile or {})}\n\n"
        f"计算结果：\n{fact_json}"
    )
    try:
        content = _chat([
            {"role": "system", "content": SAY_SYSTEM},
            {"role": "user", "content": user},
        ], api_key, base_url, model_id, headers)
    except urllib.error.HTTPError as e:
        return {"ok": False, "reason": f"http_{e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"ok": False, "reason": "network"}
    except Exception:
        return {"ok": False, "reason": "unknown"}

    line = content.strip().strip('"“”').split("\n")[0].strip()[:120]
    if not line:
        return {"ok": False, "reason": "empty"}
    if _BANNED.search(line):
        return {"ok": False, "reason": "banned"}
    if not _numbers(line) <= _numbers(fact_json):
        return {"ok": False, "reason": "invented_number"}
    return {"ok": True, "text": line, "model": model_id}
