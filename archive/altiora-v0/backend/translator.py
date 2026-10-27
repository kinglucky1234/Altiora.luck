"""
AI 翻译官 —— 只做两件事：
  1. 把用户的聊天/粘的课表 → 结构化 JSON（Event / UserProfile 字段）
  2. 把计算器算的代价分析 → 有灵魂的自然语言

**重要**：AI 不决定冲突是什么、不决定怎么重排——那是计算器的事。
AI 只负责"翻译"，计算器永远是决策者。
"""
import json
import os
from typing import Any
from schemas import CostAnalysis, Event, UserProfile
from datetime import date


# ─── Mock 模式：没有 API Key 时用规则兜底 ───────────────
# 统一读取 LLM_API_KEY，与 .env.example 和主实现 Altiora/backend/llm.py 保持一致
MOCK_MODE = os.environ.get("LLM_API_KEY", "").strip() == ""


def translate_cost_analysis_to_human(analysis: CostAnalysis, profile: UserProfile) -> dict[str, Any]:
    """
    把计算器算的代价分析翻译成前端能直接渲染的卡片 JSON。
    Mock 模式下用规则兜底（保证没 Key 也能跑）。
    """
    # ── Mock 兜底：直接把 options 的 gains/costs 原样返回 ──
    # 因为计算器给的 gains/costs 已经是自然语言了（只是没润色）
    cards = []
    emoji_map = {"A": "🟢", "B": "🟡", "C": "🔴"}

    for opt in analysis.options:
        cards.append({
            "choice": opt.choice,
            "emoji": emoji_map.get(opt.choice, "⚪"),
            "gains": opt.gains,
            "costs": opt.costs,
            "shift_to": opt.shift_to.strftime("%H:%M") if opt.shift_to else None,
        })

    # Altiora 的理念：不替用户做决定。
    # 旧版 _build_suggestion 里硬编码了 priority=1 if choice=="A"，
    # 不仅不准确（没读 Event 的真实 priority 字段），更和理念冲突——
    # 计算器只负责算账，选 A 选 B 是用户的事，不是计算器的事。
    # suggestion 字段保留占位但始终为空字符串。
    return {
        "conflict_id": analysis.conflict_id,
        "risk_note": analysis.risk_note,
        "cards": cards,
        "suggestion": "",
    }


def parse_course_text(text: str) -> list[Event]:
    """
    把用户粘的课表文字 → 结构化 Event 列表。
    Mock 模式：用简单正则兜底（支持 "周一 8:00-9:40 高数 教A101" 格式）。
    真 LLM：调用模型抽取，返回 JSON。
    """
    import re

    events: list[Event] = []
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]

    # 周几 → 日期偏移（相对今天）
    weekday_map = {
        "周一": 0, "周二": 1, "周三": 2, "周四": 3,
        "周五": 4, "周六": 5, "周日": 6,
    }

    today = date.today()
    today_weekday = today.weekday()  # 0=Monday

    for line in lines:
        # 匹配模式：周X HH:MM-HH:MM 标题 地点?
        m = re.match(
            r"(周[一二三四五六日])?\s*(\d{1,2}):(\d{2})\s*[-~到]\s*(\d{1,2}):(\d{2})\s*(.+)",
            line,
        )
        if not m:
            continue

        weekday_str = m.group(1) or ""
        start_h, start_m = int(m.group(2)), int(m.group(3))
        end_h, end_m = int(m.group(4)), int(m.group(5))
        rest = m.group(6).strip()

        # 分离标题和地点
        parts = rest.split()
        title = parts[0] if parts else rest
        location = " ".join(parts[1:]) if len(parts) > 1 else ""

        # 算日期
        target_date = today
        if weekday_str in weekday_map:
            offset = weekday_map[weekday_str] - today_weekday
            if offset < 0:
                offset += 7
            target_date = today + __import__("datetime").timedelta(days=offset)

        # 判断事件类型
        event_type = EventType.OTHER
        if any(kw in title for kw in ["课", "高数", "英语", "线代", "物理", "化"]):
            event_type = EventType.CLASS
        elif any(kw in title for kw in ["家教", "兼职", "打工"]):
            event_type = EventType.WORK
        elif any(kw in title for kw in ["开会", "meeting"]):
            event_type = EventType.MEETING
        elif any(kw in title for kw in ["自习", "学习"]):
            event_type = EventType.STUDY

        events.append(Event(
            event_id=str(__import__("uuid").uuid4())[:8],
            title=title,
            event_type=event_type,
            date=target_date,
            start=__import__("datetime").time(start_h, start_m),
            end=__import__("datetime").time(end_h, end_m),
            location=location,
            wage_per_hour=80.0 if "家教" in title else 0.0,  # Mock 默认家教 80/小时
        ))

    return events
