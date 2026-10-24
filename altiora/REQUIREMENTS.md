# Altiora — 完整需求文档（可复制给任何 AI）

## 一句话定位

**Altiora 是一款面向"AI 创新应用挑战赛·个人效能与数字孪生具身仿真"的参赛项目。它不是 AI 助手、不是人机恋、不是工具——它是用户理想中那个更好的自己在电脑里的投影。**

核心差异化（答辩必提三点）：
1. 别的日历告诉你"撞了"，我们告诉你**代价是多少**（算具体金额、睡眠损失、优先级代价），并给讨价还价式选项让你选
2. **用户自输入的规矩清单**驱动规划——不是 AI 猜你晚上刷手机，是你自己告诉我"睡觉不晚于23:00"，我帮你守住
3. **三段式架构**保证可复现：AI 翻译（Mock/LLM）→ 计算器（纯 Python 确定性逻辑）→ AI 翻译（Mock/LLM）

---

## 技术栈（固定，不换）

- **后端**：FastAPI + Pydantic（纯 Python）
- **前端**：React + Vite + TailwindCSS + shadcn/ui（深色主题、现代精致感）
- **图表**：ECharts 或 recharts（甘特图）
- **存储**：前端 IndexedDB（无后端数据库，一键复现）
- **AI 接入**：httpx 调用 LLM API（可配置 API Key），无 Key 时自动降级到 Mock 规则模式
- **零外部依赖**：不接天气/地图/外部 API，所有数据 Mock 能跑通全流程

---

## 界面设计（必须做到）

### 整体风格
- **深色极简科技风**：深灰/深蓝背景（#0f1117 或 #0b1020），白色/浅色文字，低饱和 accent color（蓝 #3b82f6、绿 #10b981、橙 #f97316、红 #ef4444）
- 现代精致感：shadcn/ui 风格，圆角 8-12px，subtle 阴影，微动画过渡（0.15s）
- 不恐怖的卡通分身：圆形 emoji 或极简 SVG 小生物（不是真人、不是机械臂），光晕表示状态

### 页面布局（单页，4 个 Tab）

```
┌─ 顶部凝视条（sticky 固定）─────────────────────────────────┐
│ 未来的你：偏差 -15%  ● 今日 2 处冲突（红闪当冲突时）      │
├─────────────────────────────────────────────────────────────┤
│ [Plan 规划] [Chat 聊天] [Clone 分身] [Me 画像]              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Plan Tab 默认显示]                                        │
│                                                             │
│  📅 今天（10/21 周二）                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 06:00                                               │  │
│  │  ████████ 高数课 教A101    08:00-09:40               │  │
│  │        ████████ 家教 东门  10:00-12:00   [时薪80]     │  │
│  │                    ██████ 开会 302  14:00-15:00       │  │
│  │                         ████ 家教补  14:30-16:30 [冲突]│  │
│  │  ██████████ 写代码 宿舍   19:00-21:00                 │  │
│  │  ████████ 睡觉             23:00-07:00 [硬约束]       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ── 光带（颜色自动变：绿色正常/红色冲突/暗灰没任务）──      │
│                                                             │
│  ── 分身 ──                                                 │
│  [🧑‍💻 emoji]  今天 2 处冲突 · 完成率 60%    [绿色光晕]     │
│                                                             │
│  ── 冲突卡片（核心视觉！设计精致！）──                       │
│  🔴 开会(14:00) vs 家教补(14:30) 撞了30分钟                 │
│                                                             │
│  ┌─ 选项A ───────────────────────────────────────────────┐ │
│  │ 🟢 去开会                                             │ │
│  │ 📈 收益：保住优先级1的事（会议不缺席）                 │ │
│  │ 📉 代价：损失160元（家教补2小时×时薪80）               │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌─ 选项B ───────────────────────────────────────────────┐ │
│  │ 🟡 去家教补                                           │ │
│  │ 📈 收益：赚160元                                      │ │
│  │ 📉 代价：放弃优先级1的事（事后可能后悔）               │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌─ 选项C（有空间才显示）────────────────────────────────┐ │
│  │ 🔴 挪家教补到15:30                                     │ │
│  │ 📈 收益：两件事都保住                                  │ │
│  │ 📉 代价：连轴转，睡觉可能挤到23:30后                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  💡 Altiora 建议：选A——守住优先级更高的事                   │
│     根据你自己说的"晚上容易刷手机"，别让自己太辛苦          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 功能定义（精确到输入/输出/谁来做）

### 核心架构约束（不可改！！！）

```
用户输入 → 【AI 翻译官】→ 【计算器（纯 Python，确定性）】→ 【AI 翻译官】→ 前端
```

- 计算器 **永远不调 LLM**，同输入必须同输出（可复现性 25% 分的保障）
- AI 翻译官做两件事：① 把用户文字→结构化 JSON；② 把计算器的数字→有人味的话
- Mock 模式兜底：无 API Key 时用正则/规则，不报错、能完整跑通

### 功能清单

#### F1 · Clone 分身（第一次打开）
**UI**：Clone Tab，4 张卡片表单
**输入**：
- 你的名字
- 硬约束：睡觉不能晚于几点（time input）
- 精力最好时段（text input）
- 已知弱点（textarea，每行一个）
- 长期目标（text input）
- 分身 emoji（5 个按钮选：🧑‍💻📚🏃😴💻）
**谁处理**：AI 翻译官（Mock 模式直接接收）
**输出**：UserProfile JSON → 存 IndexedDB
**对应赛题**：数字孪生分身

#### F2 · 课表解析（Mock 正则 + 真 LLM）
**UI**：Chat Tab 粘课表 → 发送
**输入**：课表文字，格式示例 `"周一 08:00-09:40 高数 教A101\n周二 10:00-12:00 家教"`
**谁处理**：AI 翻译官
- Mock 模式：正则 `(周[一二三四五六日])?\s*(\d{1,2}):(\d{2})\s*[-~到]\s*(\d{1,2}):(\d{2})\s*(.+)` 匹配
- 真 LLM：Prompt 约束输出 Event JSON 列表
**输出**：Event[] JSON → 甘特图渲染

#### F3 · 冲突检测（计算器核心）
**输入**：Event[] 列表 + UserProfile
**谁处理**：计算器（纯 Python）
**逻辑**：
1. 遍历同日期事件对
2. 计算 start/end 时间重叠分钟数
3. 重叠 > 0 → Conflict 记录
**输出**：Conflict[] JSON
**对应赛题**：自适应日程冲突调整

#### F4 · 代价测算（计算器核心）
**输入**：单个 Conflict + Event[] + UserProfile
**谁处理**：计算器（纯 Python，不可调 LLM）
**逻辑**：
1. 比较冲突两件事的 priority（1=硬约束 2=中等 3=软约束）
2. 生成选项 A（保高优先级）：gains=["保住X（优先级Y）"] / costs=["损失Z元（放弃X的时薪）" or "放弃X"]
3. 生成选项 B（保低优先级）：gains=["保住X"] / costs=["放弃X"+"放弃了优先级更高的事，事后可能后悔" if 放弃的是高优]
4. 尝试生成选项 C（挪时间）：往冲突结束后 +15min，如果不撞睡觉硬约束 → gains=["全都保住，挪到XX:XX"] / costs=["连轴转，睡觉可能被挤"]
5. 定性风险：有金钱损失 → "存在金钱损失的选项，请综合长期目标考虑"
**输出**：CostAnalysis JSON（含 options[] + risk_note）

#### F5 · 灵魂化表达（AI 翻译官）
**输入**：CostAnalysis JSON + UserProfile
**谁处理**：AI 翻译官
- Mock 模式：直接透传计算器给的 gains/costs（已是自然语言）
- 真 LLM：润色 gains/costs 成更有人味的话 + 根据画像卡里的 known_weakness 生成建议
**输出**：前端可直接渲染的卡片 JSON（cards[] + suggestion）

#### F6 · 分身状态
**输入**：当日冲突数
**谁处理**：计算器（纯逻辑判断）
**逻辑**：conflict > 0 → 红光晕 + 光带红 + 凝视条红闪；conflict = 0 → 绿光晕 + 光带绿
**输出**：前端渲染分身 emoji + 光晕颜色 + 光带颜色 + 凝视条文字

---

## 数据 Schema（精确，直接用）

### Event（日程事件）
```python
class Event(BaseModel):
    event_id: str           # 唯一ID
    title: str              # "高数课" / "家教"
    event_type: str         # class / work / meeting / study / sleep / other
    date: date              # 哪一天
    start: time             # 几点开始
    end: time               # 几点结束
    location: str           # 地点（可选）
    priority: int           # 1=硬约束 2=中等 3=软约束
    wage_per_hour: float    # 时薪（算代价用，0=无）
```

### Conflict（冲突）
```python
class Conflict(BaseModel):
    conflict_id: str
    type: str               # overlap
    event_a_id: str
    event_b_id: str
```

### Option（单个选项）
```python
class Option(BaseModel):
    choice: str             # "A" / "B" / "C"
    event_to_keep: str
    event_to_drop: str | None
    event_to_shift: str | None
    shift_to: time | None
    gains: list[str]        # ["保住了「开会」（优先级 1）"]
    costs: list[str]        # ["损失 160 元（放弃「家教补」的时薪）"]
```

### CostAnalysis（代价分析）
```python
class CostAnalysis(BaseModel):
    conflict_id: str
    options: list[Option]
    risk_note: str          # "存在金钱损失的选项，请综合长期目标考虑"
```

### UserProfile（用户画像）
```python
class UserProfile(BaseModel):
    name: str
    hard_sleep_deadline: time           # 睡觉不能晚于
    hard_morning_start: time            # 早起不能早于
    preferred_focus_hours: str          # "09:00-12:00"
    known_weakness: list[str]           # ["晚上容易刷手机", "连续学3小时会垮"]
    long_term_goal: str                 # "拿传智杯奖" / "考研985"
    avatar_emoji: str                   # "🧑‍💻"
```

---

## API 接口（精确，直接用）

### GET /api/mock
返回完整 demo 数据，前端一启动就能渲染。
```json
{
  "profile": { /* UserProfile */ },
  "events": [ /* Event[] */ ],
  "gantt": [
    { "id": "e1", "name": "高数课", "type": "class",
      "start_min": 480, "end_min": 580, "priority": 1, "conflict": false }
  ],
  "conflict_cards": [ /* CostAnalysis 经过翻译后的卡片 */ ],
  "total_conflicts": 1
}
```

### POST /api/parse-course
课表文字 → Event[]
- 入参：`text: str`（课表文字）
- 返回：`{ "events": [ /* Event JSON */ ] }`

### POST /api/analyze
events + profile → 冲突代价卡片
- 入参：`events: Event[]` + `profile: UserProfile`
- 返回：`{ "conflict_cards": [ /* 翻译后的卡片 */ ], "total_conflicts": 1 }`

---

## Mock 数据（必须用，让 demo 能直接跑）

```
今日日程：
- 高数课     08:00-09:40   教A101       优先级1
- 家教       10:00-12:00   东门咖啡馆   优先级2  时薪80元
- 开会       14:00-15:00   302会议室    优先级1
- 家教补     14:30-16:30   东门咖啡馆   优先级2  时薪80元
- 写代码     19:00-21:00   宿舍         优先级3
- 睡觉       23:00起                    优先级1（硬约束）

用户画像：
- 硬约束：睡觉不晚于23:00
- 精力最好：09:00-12:00
- 弱点：晚上容易刷手机、连续学3小时会垮
- 目标：拿传智杯奖

自动检测：开会(14:00) vs 家教补(14:30) 撞了30分钟
自动生成3个选项 + 代价 + Altiora建议
```

---

## 后端骨架（已完成，可以直接用）

后端已在 `/workspace/altiora/backend/` 下，包含：

```
backend/
├── main.py         # FastAPI 主入口 + /api/mock + CORS + 静态文件
├── schemas.py      # Event / Conflict / CostAnalysis / Option / UserProfile 定义
├── calculator.py   # ★ 计算器核心（detect_conflicts + compute_cost_analysis + analyze_day）
├── translator.py   # AI 翻译官（Mock 正则解析 + gains/costs 透传 + 冷血建议生成）
└── requirements.txt
```

计算器核心逻辑（Python）：
- `detect_conflicts(events)` → 遍历同日期事件对，算 start/end 时间重叠分钟数
- `compute_cost_analysis(conflict, events, profile)` → 比较 priority → 生成 A/B/C 三个选项 → 算 gains/costs → 定性风险
- `analyze_day(events, profile)` → 上面两个合起来

**后端不用改，AI 只要把前端重新做得漂亮就行。**

---

## 已完成的本地 Git Commit

```
commit 502ba68
Author: Altiora Dev <altiora@local.dev>
Date: 2026-10-21

feat: scaffold Altiora — 三段式架构 + 计算器核心 + 深色极简前端

10 files changed, 1231 insertions(+)
```

---

## 给 AI 的 Prompt（直接复制）

```
请基于 FastAPI + React + Vite + TailwindCSS + shadcn/ui，开发一个叫 Altiora 的个人效能应用。

## 核心架构（不可改）
用户输入 → AI翻译官(Mock/LLM) → 计算器(纯Python确定性逻辑) → AI翻译官 → 前端
计算器永远不调LLM，同输入必须同输出。无API Key时自动降级到Mock规则模式。

## 后端（已完成，直接用 /workspace/altiora/backend/）
- main.py: FastAPI + /api/mock + CORS + 静态文件挂载 frontend/
- schemas.py: Event / Conflict / CostAnalysis / Option / UserProfile
- calculator.py: detect_conflicts() + compute_cost_analysis() + analyze_day()
- translator.py: Mock 正则解析课表 + gains/costs 透传 + 冷血建议
- requirements.txt: fastapi uvicorn pydantic httpx

启动: cd backend && pip install -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## 前端要求（你要做的）
- React + Vite + TailwindCSS + shadcn/ui
- 深色科技风（#0f1117 / #0b1020 背景，蓝#3b82f6绿#10b981橙#f97316红#ef4444 点缀）
- 4 Tab：Plan / Chat / Clone / Me
- Plan Tab 默认显示：ECharts 或 recharts 甘特图 + 冲突卡片（核心视觉，设计精致！）+ 分身 emoji + 光晕 + 光带
- 顶部 sticky 凝视条："未来的你：偏差 -15% ● 今日 X 处冲突"（有冲突时红闪）
- 分身 emoji（5个可选：🧑‍💻📚🏃😴💻）+ 光晕颜色（绿=正常 红=冲突）
- 分身状态由计算器 JSON 驱动，不是写死动画
- 冲突卡片设计精致：🟢🟡🔴 emoji + 📈📉 收益代价标签 + Altiora 冷血建议
- Clone Tab：4张卡片表单（名字/睡觉时间/精力时段/弱点/目标/emoji选择）
- Chat Tab：深色聊天框 + mock 回复（粘课表→调后端解析；说累→记状态）
- Me Tab：展示用户画像 JSON

## API
- GET /api/mock → 完整 demo 数据（profile + events + gantt + conflict_cards + total_conflicts）
- POST /api/parse-course {"text": "..."} → Event[]
- POST /api/analyze events[] + profile → 冲突卡片

## Mock 数据（后端已内置）
开会(14:00,优先级1) vs 家教补(14:30,优先级2,时薪80元) 撞30分钟
→ 计算器自动生成3个选项 + 代价 + Altiora建议

## 关键设计约束
1. 冲突卡片必须是核心视觉，设计精致、层次清晰、有 emoji 和标签
2. 深色极简科技风，不花哨，但现代精致（shadcn/ui 风格）
3. 分身用 emoji + CSS 光晕实现，不是 SVG 手绘
4. 所有状态变化由后端 JSON 驱动，前端只渲染
5. 零外部依赖：不接天气/地图，所有数据本地 Mock 能跑通全流程
6. 无 API Key 时也能完整 demo 出"冲突检测 + 代价测算 + 讨价还价"链路
```

---

## 给你自己的备忘

- **参赛赛道**：AI 创新应用挑战赛 · 个人效能与数字孪生具身仿真
- **评分重点**：实用价值 25% + 可复现性 25% + 演进链路 25% + 意图控制 20% + 工程质量 5%
- **三段式架构**是可复现性的保障，**计算器**是核心，不能让 LLM 算冲突
- **代价测算**是差异化亮点，别降成普通冲突提示
- **演进链路**：每次小改动独立 commit，对应一次 AI 对话，答辩时能演示
- **时间**：从今天 10/21 到省赛 11/18，共 4 周
