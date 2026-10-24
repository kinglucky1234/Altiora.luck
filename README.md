# Altiora · 未来的我

> 用户理想中更好的自己在电脑里的投影 —— 数字孪生分身 + 代价测算引擎
> 赛道：个人效能与数字孪生具身仿真（传智杯 Vibe Coding 挑战赛 · 赛道 8）

## 1. 一句话定位

市面上的 AI 助手、日历、习惯养成 App 都在**替你做决定**。

Altiora 不替你决定 —— **它只把每个选择的代价算清楚，让你自己挑**。

## 2. 三段式架构

```
用户说话
   ↓
① AI 翻译官    把自然语言 → 结构化事件 / 情绪标签（规则 + 可选大模型）
   ↓
② 计算器       纯 Python，永不调用大模型；同一输入永远同一输出
   ↓
③ AI 翻译官    把计算结果 → 人话（代价卡片 / 一句接住情绪的话）
   ↓
用户看到
```

**关键约束：第 ② 步不含任何概率成分。** 家教 2 小时 × 80 元 = 160 元，第 100 次算也是 160。这是用户能信任它的唯一理由。

## 3. 十 分钟极速复现

### 0-2 分钟：环境准备

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10/11、macOS 12+、Linux |
| Python | **3.8 及以上**（`python --version` 可验证） |
| 浏览器 | Chrome / Edge（语音输入依赖 Web Audio + MediaRecorder） |
| 磁盘 | 约 150 MB |
| 网络 | 仅首次装依赖需要；**跑起来后完全离线** |

> Windows 安装 Python 时务必勾选 **Add Python to PATH**。

### 2-5 分钟：拉代码 + 装依赖

```bash
git clone https://github.com/kinglucky1234/Altiora.luck.git
cd Altiora.luck/Altiora
pip install -r requirements.txt
```

依赖清单（`requirements.txt`）：

```
fastapi            # Web 服务
uvicorn            # ASGI 服务器
python-multipart   # 接收前端上传的录音
vosk               # 离线中文语音识别
```

### 5-6 分钟：启动

```bash
python server.py
```

看到 `Uvicorn running on http://0.0.0.0:8000` 即可。

打开浏览器访问 **http://localhost:8000**。

> Windows 也可直接双击 `run.bat`，macOS 右键 `run.command` → 打开。

### 6-10 分钟：验证四条链路

| # | 操作 | 预期结果 |
|---|---|---|
| 1 | 点麦克风，说「今天没睡好」 | 约 1-3 秒后出现汉字气泡，AI 用一句话接住情绪 |
| 2 | 打字「下午两点开会，两点半家教」 | 识别为时间冲突，出现代价卡片 |
| 3 | 打字「记住，我晚上容易刷手机」 | 一句话确认，写入本地画像 |
| 4 | 点输入框右侧气泡图标 | 进入全屏对话记录，AI 消息可回放朗读 |

## 4. 环境变量

复制模板：

```bash
cp .env.example .env
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | `8000` | 服务端口，被占用时改成 8001 等 |
| `VOSK_MODEL_PATH` | 内置模型路径 | 换用其他 Vosk 中文模型时填写绝对路径 |
| `LLM_API_KEY` | 空 | **预留**，当前版本未启用；留空则走内置话术模板 |

> 全部留空也能完整跑通 —— 这是本项目「零外部依赖」的设计目标，也是断网/无 Key 场景下的兜底。

## 5. 目录结构

```
Altiora.luck/
├── Altiora/                       # ★ 可运行版本（评委从这里启动）
│   ├── server.py                  # 本地服务 + 离线语音识别接口
│   ├── index.html                 # 单文件前端（球 / 对话 / 冲突卡片）
│   ├── run.bat / run.command      # 一键启动脚本
│   └── backend/model/             # Vosk 中文离线模型
├── altiora/backend/               # 三段式架构与计算器实现
│   ├── calculator.py              # 代价测算核心（确定性）
│   ├── schemas.py                 # 数据结构定义
│   └── translator.py              # 自然语言 ↔ 结构化
├── Altiora-未来的我.html           # 单文件原型（开发过程版本）
├── Altiora-需求文档.docx           # 需求与设计文档
├── prompt-snapshots/              # AI 对话历史快照（比赛材料）
├── .env.example                   # 环境变量模板
└── README.md
```

## 6. 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `python: command not found` | 未装 Python 或未加 PATH | 重装并勾选 Add Python to PATH，或用 `python3` |
| `ModuleNotFoundError: fastapi` | 依赖没装到当前解释器 | `python -m pip install -r requirements.txt` |
| 端口被占用 (`Address already in use`) | 8000 已被其它程序占用 | `set PORT=8001` 后重启，或 Windows `netstat -ano | findstr :8000` |
| 页面能开，点麦克风没反应 | 浏览器不允许麦克风 / 非 localhost | 用 Chrome 打开 `http://localhost:8000`，并在地址栏允许麦克风 |
| 语音一直返回空文本 | 模型目录缺失 | 确认 `Altiora/backend/model/vosk-model-small-cn-0.22/` 存在（约 42 MB） |
| 识别很慢（>5 秒） | 首次加载模型 | 第一次识别会加载模型，之后每次约 1-3 秒 |

## 7. 评审材料索引

| 比赛要求 | 仓库位置 | 状态 |
|---|---|---|
| 代码仓库 Public | 本仓库 | ✅ |
| 细粒度 Git 提交历史 | `git log --oneline` | ✅ |
| AI Prompt 历史快照（≥3 组迭代） | `prompt-snapshots/` | ✅ |
| 10 分钟复现指南 | 本文档第 3 节 | ✅ |
| 环境变量模板 | `.env.example` | ✅ |
| 演示视频（5-8 分钟，含 ≥2 分钟 AI 协同复现） | 待补 | ⏳ |
| 技术文档 PDF（≤30 页） | 待补 | ⏳ |

## 8. 设计原则（为什么这样做）

- **不给记分板，只给账单。** 完成率会掉分，一掉分用户就想「重开」；代价不会判你不及格。
- **没有重开键。** 断了几天回来显示「接着走」，不显示「已中断」。
- **代价卡片只在真冲突时出现。** 情绪场景只出一句话 —— 人难受时不需要表格。
- **球不加五官。** 停在抽象具身，避开恐怖谷。
