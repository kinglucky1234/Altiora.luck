# Altiora

> 你理想中的自己，先在数字世界里跑起来。

个人效能 · 数字孪生分身 · 代价测算引擎。AI 创新应用挑战赛参赛项目。

## 这是什么

Altiora 不是 AI 助手，也不是人机恋。它是你理想中那个更好的自己在电脑里的投影——clone 你的规矩清单，替你算日程冲突的代价，在你快崩的时候跟你讨价还价。

**三段式架构**（核心，保证可复现）：

```
你的输入（聊天 / 粘课表 / Clone 表单）
        ↓
    AI 翻译官（Mock / LLM）
    把文字翻译成结构化 JSON
        ↓
    计算器（纯 Python，确定性逻辑）
    · 冲突检测
    · 代价测算（每个选项的收益/代价）
    · 风险定性评估
        ↓
    AI 翻译官（Mock / LLM）
    把数字翻译成有人味的卡片
        ↓
    前端（深色极简 + ECharts 甘特图）
```

## 快速开始

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 打开浏览器

```
http://localhost:8000
```

**无 API Key 也能跑**——Mock 模式用正则解析课表、用规则生成代价选项。

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/mock` | 返回完整 mock 数据（profile + events + gantt + conflict_cards） |
| POST | `/api/parse-course` | 课表文字 → Event 列表 |
| POST | `/api/analyze` | 传入 events + profile → 冲突代价卡片 |

## 目录

```
altiora/
├── backend/
│   ├── main.py         # FastAPI 主入口
│   ├── schemas.py      # 数据定义
│   ├── calculator.py   # 计算器核心（纯 Python 确定性逻辑）
│   ├── translator.py   # AI 翻译官（Mock 模式）
│   └── requirements.txt
└── frontend/
    ├── index.html      # 深色极简 4 Tab
    ├── css/style.css
    └── js/app.js       # ECharts 甘特图 + 冲突卡片 + Clone + 聊天
```

## 当前进度（2026-10-21）

- ✅ 三段式架构骨架搭完
- ✅ 计算器核心：冲突检测 + 代价测算（3 个选项，含金钱损失、优先级、挪时间）
- ✅ Mock 模式全链路跑通（无 Key 也能 demo）
- ✅ 前端深色极简 + ECharts 甘特图 + 冲突卡片 + 分身 emoji + Clone 表单 + 聊天框
- ✅ 三个 Tab：Plan / Chat / Clone / Me

## 下一步

- [ ] 接真 LLM（配置 API Key 替换 Mock 模式）
- [ ] Clone 表单真入库 + 真传入 `/api/analyze`
- [ ] 聊天框接后端（粘课表 → 真解析 → 真计算）
- [ ] 分身 emoji 换成你自己画的卡通形象
- [ ] IndexedDB 持久化
- [ ] README 完善 + demo 视频

## 参赛信息

- 赛道：AI 创新应用挑战赛 · 个人效能与数字孪生具身仿真
- 关键词：个人效能 / 数字孪生分身 / 自适应日程冲突 / 日程·笔记·日常
