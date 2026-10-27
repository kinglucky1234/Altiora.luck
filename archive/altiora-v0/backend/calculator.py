"""
计算器核心 —— 保证同输入同输出。
不调 LLM，纯 Python 确定性逻辑。
"""
from datetime import datetime, time, timedelta, date
from schemas import (
    Event, EventType, Conflict, ConflictType,
    Option, CostAnalysis, UserProfile
)
import uuid


# ─── 工具函数 ────────────────────────────────────────────
def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _from_minutes(m: int) -> time:
    return time(hour=m // 60, minute=m % 60)


def _overlap(a_start: time, a_end: time, b_start: time, b_end: time) -> int:
    """两个时间段重叠多少分钟。0 表示不重叠。"""
    a = (_to_minutes(a_start), _to_minutes(a_end))
    b = (_to_minutes(b_start), _to_minutes(b_end))
    start = max(a[0], b[0])
    end = min(a[1], b[1])
    return max(0, end - start)


# ─── 第一步：冲突检测 ────────────────────────────────────
def detect_conflicts(events: list[Event]) -> list[Conflict]:
    """
    扫一遍日程，返回所有时间重叠的冲突。
    通勤冲突暂时先硬编码一个地点距离表，后续可以扩展。
    """
    conflicts: list[Conflict] = []

    # 时间重叠
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1, e2 = events[i], events[j]
            if e1.date != e2.date:
                continue
            overlap_min = _overlap(e1.start, e1.end, e2.start, e2.end)
            if overlap_min > 0:
                conflicts.append(Conflict(
                    conflict_id=str(uuid.uuid4())[:8],
                    type=ConflictType.OVERLAP,
                    event_a_id=e1.event_id,
                    event_b_id=e2.event_id,
                    description=(
                        f"{e1.title}({e1.start}-{e1.end}) 与 "
                        f"{e2.title}({e2.start}-{e2.end}) 重叠 {overlap_min} 分钟"
                    )
                ))

    return conflicts


# ─── 第二步：代价测算（核心引擎） ────────────────────────
def compute_cost_analysis(
    conflict: Conflict,
    events: list[Event],
    profile: UserProfile,
) -> CostAnalysis:
    """
    给定一个冲突，算出 2-3 个选项，每个选项的收益和代价。
    纯逻辑，不调 LLM，保证同输入同输出。
    """
    e_a = next(e for e in events if e.event_id == conflict.event_a_id)
    e_b = next(e for e in events if e.event_id == conflict.event_b_id)

    options: list[Option] = []

    # ── 选项 A：保留优先级高的那件事，放弃另一件 ──────────
    if e_a.priority <= e_b.priority:
        keep, drop = e_a, e_b
    else:
        keep, drop = e_b, e_a

    gains_a = [f"保住了「{keep.title}」（优先级 {keep.priority}）"]
    costs_a = []
    if drop.wage_per_hour > 0:
        lost = drop.wage_per_hour * ((_to_minutes(drop.end) - _to_minutes(drop.start)) / 60)
        costs_a.append(f"损失 {lost:.0f} 元（放弃「{drop.title}」的时薪）")
    else:
        costs_a.append(f"放弃了「{drop.title}」")

    options.append(Option(
        choice="A",
        event_to_keep=keep.event_id,
        event_to_drop=drop.event_id,
        gains=gains_a,
        costs=costs_a,
    ))

    # ── 选项 B：保留优先级低的那件事，放弃另一件 ──────────
    if e_a.priority <= e_b.priority:
        keep2, drop2 = e_b, e_a
    else:
        keep2, drop2 = e_a, e_b

    gains_b = [f"保住了「{keep2.title}」"]
    costs_b = []
    if drop2.wage_per_hour > 0:
        lost = drop2.wage_per_hour * ((_to_minutes(drop2.end) - _to_minutes(drop2.start)) / 60)
        costs_b.append(f"损失 {lost:.0f} 元（放弃「{drop2.title}」的时薪）")
    else:
        costs_b.append(f"放弃了「{drop2.title}」")

    # 额外代价：如果放弃的是优先级高的
    if drop2.priority < keep2.priority:
        costs_b.append("放弃了优先级更高的事，事后可能后悔")

    options.append(Option(
        choice="B",
        event_to_keep=keep2.event_id,
        event_to_drop=drop2.event_id,
        gains=gains_b,
        costs=costs_b,
    ))

    # ── 选项 C：挪其中一件事（挪完不撞任何硬约束也不撞别的事） ──
    shiftable = e_b if e_b.priority >= 2 else None
    if shiftable is None or shiftable.priority >= 2:
        shiftable = e_a if e_a.priority >= 2 else None

    if shiftable:
        # 往冲突结束后挪 15 分钟
        other = e_a if shiftable.event_id == e_b.event_id else e_b
        new_start_min = _to_minutes(other.end) + 15
        new_end_min = new_start_min + (_to_minutes(shiftable.end) - _to_minutes(shiftable.start))
        new_start = _from_minutes(new_start_min)
        new_end = _from_minutes(new_end_min)

        # ① 硬约束：睡觉时间
        sleep_deadline_min = _to_minutes(profile.hard_sleep_deadline)
        if new_end_min > sleep_deadline_min:
            pass  # 撞睡觉了，不给选项 C
        else:
            # ② 重跑 detect_conflicts：挪完会不会撞上别的事件
            #    之前只查了睡觉，那是偷懒；现在算真的
            shifted_copy = Event(
                event_id=shiftable.event_id,
                title=shiftable.title,
                event_type=shiftable.event_type,
                date=shiftable.date,
                start=new_start,
                end=new_end,
                location=shiftable.location,
                priority=shiftable.priority,
                wage_per_hour=shiftable.wage_per_hour,
                notes=shiftable.notes,
            )
            rest = [e for e in events if e.event_id != shiftable.event_id]
            new_conflicts = detect_conflicts(rest + [shifted_copy])
            # 排除原来那场冲突本身，只看挪完新产生的
            original_pair = {conflict.event_a_id, conflict.event_b_id}
            truly_new = [
                c for c in new_conflicts
                if {c.event_a_id, c.event_b_id} != original_pair
            ]
            if truly_new:
                pass  # 挪完又撞新的了，不给选项 C
            else:
                gains_c = [
                    f"全都不放弃——「{shiftable.title}」往后挪 15 分钟到 {new_start.strftime('%H:%M')}",
                    "两件事都保住了",
                ]
                costs_c = [
                    "连轴转，休息时间被压缩",
                    "心理压力增加（连续做两件事）",
                ]
                if new_end_min > sleep_deadline_min - 60:
                    costs_c.append(
                        f"睡觉时间可能被挤到 {new_end.strftime('%H:%M')} 之后"
                    )

                options.append(Option(
                    choice="C",
                    event_to_keep=e_a.event_id,
                    event_to_shift=shiftable.event_id,
                    shift_to=new_start,
                    gains=gains_c,
                    costs=costs_c,
                ))

    # ── 定性风险评估（给 AI 翻译官用） ────────────────────
    max_cost = max(
        len(options[0].costs),
        len(options[1].costs),
        len(options[-1].costs) if len(options) > 2 else 0,
    )
    if any("元" in c for o in options for c in o.costs):
        risk_note = "存在金钱损失的选项，请综合长期目标考虑"
    elif max_cost >= 3:
        risk_note = "所有选项代价都不小，建议慎重决定"
    else:
        risk_note = "两个选项代价相当，凭当前优先级选就行"

    return CostAnalysis(
        conflict_id=conflict.conflict_id,
        options=options,
        risk_note=risk_note,
    )


# ─── 第一步+第二步合起来 ─────────────────────────────────
def analyze_day(
    events: list[Event],
    profile: UserProfile,
) -> list[CostAnalysis]:
    """
    对给定日期的所有事件，检测冲突并算出代价。
    返回一个 CostAnalysis 列表，每个元素对应一个冲突。
    """
    conflicts = detect_conflicts(events)
    analyses = []
    for c in conflicts:
        analyses.append(compute_cost_analysis(c, events, profile))
    return analyses
