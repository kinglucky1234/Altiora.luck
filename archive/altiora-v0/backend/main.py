"""
Altiora 后端主入口 —— FastAPI
三段式架构：AI抽取 → 计算器 → AI翻译
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import date
from pathlib import Path

from schemas import Event, UserProfile, CostAnalysis
from calculator import analyze_day, detect_conflicts, compute_cost_analysis
from translator import translate_cost_analysis_to_human, parse_course_text

app = FastAPI(title="Altiora", version="0.1.0")

# CORS（前端原生 HTML 跑本地，跨域方便）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 前端静态文件
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# ─── Mock 数据（让无 API Key 也能跑） ──────────────────
def _mock_events() -> list[Event]:
    from datetime import time as dt_time
    import uuid as _uuid
    today = date.today()

    return [
        Event(event_id="e1", title="高数课", event_type="class", date=today,
              start=dt_time(8, 0), end=dt_time(9, 40), location="教A101", priority=1),
        Event(event_id="e2", title="家教", event_type="work", date=today,
              start=dt_time(10, 0), end=dt_time(12, 0), location="东门咖啡馆",
              priority=2, wage_per_hour=80.0),
        Event(event_id="e3", title="开会", event_type="meeting", date=today,
              start=dt_time(14, 0), end=dt_time(15, 0), location="302会议室", priority=1),
        Event(event_id="e4", title="家教补", event_type="work", date=today,
              start=dt_time(14, 30), end=dt_time(16, 30), location="东门咖啡馆",
              priority=2, wage_per_hour=80.0),
        Event(event_id="e5", title="写代码", event_type="study", date=today,
              start=dt_time(19, 0), end=dt_time(21, 0), location="宿舍", priority=3),
        Event(event_id="e6", title="睡觉", event_type="sleep", date=today,
              start=dt_time(23, 0), end=dt_time(23, 59), priority=1),
    ]


def _mock_profile() -> UserProfile:
    from datetime import time as dt_time
    return UserProfile(
        user_id="default",
        name="同学",
        hard_sleep_deadline=dt_time(23, 0),
        hard_morning_start=dt_time(7, 0),
        preferred_focus_hours="09:00-12:00",
        known_weakness=["晚上容易刷手机", "连续学3小时会垮"],
        long_term_goal="拿传智杯奖",
        updated_at="2026-10-21",
    )


# ─── API 路由 ─────────────────────────────────────────────
@app.get("/api/mock")
def get_mock():
    """返回 mock 数据，前端能直接渲染。"""
    events = _mock_events()
    profile = _mock_profile()
    conflicts = detect_conflicts(events)
    analyses = [compute_cost_analysis(c, events, profile) for c in conflicts]
    human_cards = [translate_cost_analysis_to_human(a, profile) for a in analyses]

    # 冲突的 event_id 集合
    conflict_event_ids = set()
    for c in conflicts:
        conflict_event_ids.add(c.event_a_id)
        conflict_event_ids.add(c.event_b_id)

    # 甘特图需要的简易数据
    gantt = []
    for e in events:
        gantt.append({
            "id": e.event_id,
            "name": e.title,
            "type": e.event_type.value,
            "start": e.start.strftime("%H:%M"),
            "end": e.end.strftime("%H:%M"),
            "start_min": e.start.hour * 60 + e.start.minute,
            "end_min": e.end.hour * 60 + e.end.minute,
            "priority": e.priority,
            "conflict": e.event_id in conflict_event_ids,
        })

    return {
        "profile": profile.model_dump(),
        "events": [e.model_dump() for e in events],
        "gantt": gantt,
        "conflict_cards": human_cards,
        "total_conflicts": len(analyses),
    }


@app.post("/api/parse-course")
def parse_course(text: str):
    """把课表文字 → Event 列表（AI 翻译官 · Mock 模式）。"""
    events = parse_course_text(text)
    return {"events": [e.model_dump() for e in events]}


@app.post("/api/analyze")
def analyze(events: list[Event], profile: UserProfile):
    """分析日程，返回冲突+代价卡片。"""
    analyses = analyze_day(events, profile)
    human_cards = [translate_cost_analysis_to_human(a, profile) for a in analyses]
    return {"conflict_cards": human_cards, "total_conflicts": len(analyses)}


# ─── 前端静态文件 ─────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
