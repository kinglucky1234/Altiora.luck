"""
数据 Schema —— 整个项目的地基。
计算器、AI 翻译官、前端渲染全围着这几个类型转。
"""
from pydantic import BaseModel, Field
from datetime import time, date
from enum import Enum


# ─── 事件：日程里的一件事 ────────────────────────────────
class EventType(str, Enum):
    CLASS = "class"          # 上课
    WORK = "work"            # 兼职/家教
    MEETING = "meeting"      # 开会
    STUDY = "study"          # 学习/自习
    COMMUTE = "commute"      # 通勤
    SLEEP = "sleep"          # 睡觉
    OTHER = "other"          # 其他


class Event(BaseModel):
    event_id: str
    title: str                         # "高数课" / "家教" / "开会"
    event_type: EventType
    date: date                         # 哪一天
    start: time                        # 几点开始
    end: time                          # 几点结束
    location: str = ""                 # 地点（可选，用于通勤计算）
    priority: int = 2                  # 1=硬约束(不可动) 2=中等 3=软约束(可调)
    wage_per_hour: float = 0.0         # 时薪（算代价用）
    notes: str = ""


# ─── 冲突检测结果 ────────────────────────────────────────
class ConflictType(str, Enum):
    OVERLAP = "overlap"                # 时间重叠
    COMMUTE = "commute"                # 通勤不够


class Conflict(BaseModel):
    conflict_id: str
    type: ConflictType
    event_a_id: str
    event_b_id: str
    description: str                   # 给 AI 翻译官用的描述


# ─── 代价测算结果 ────────────────────────────────────────
class Option(BaseModel):
    choice: str                        # "A" / "B" / "C"
    event_to_keep: str                 # 保留哪个 event_id
    event_to_drop: str | None = None   # 放弃哪个（挪不算放弃）
    event_to_shift: str | None = None  # 挪哪个
    shift_to: time | None = None
    gains: list[str] = []              # 收益（给 AI 翻成自然语言）
    costs: list[str] = []              # 代价（给 AI 翻成自然语言）


class CostAnalysis(BaseModel):
    conflict_id: str
    options: list[Option]              # 2-3 个选项
    risk_note: str                     # 定性风险说明（给 AI 翻）


# ─── 用户画像（Clone tab 填的规矩清单） ──────────────────
class UserProfile(BaseModel):
    user_id: str = "default"
    name: str = ""
    # 硬约束
    hard_sleep_deadline: time = time(23, 0)     # 睡觉不能晚于
    hard_morning_start: time = time(7, 0)       # 早起不能早于
    # 软约束（用户自己说的节奏）
    preferred_focus_hours: str = "09:00-12:00"  # 精力最好时段
    known_weakness: list[str] = []              # ["晚上容易刷手机", "连续学3小时会垮"]
    # 长期目标（一句话就行）
    long_term_goal: str = ""
    # 最近一次更新时间
    updated_at: str = ""
