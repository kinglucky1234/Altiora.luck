# Altiora · 未来的我

> 用户理想中更好的自己在电脑里的投影——数字孪生分身 + 代价测算引擎
> 赛道：个人效能与数字孪生具身仿真（传智杯赛道 8）

## 核心定位

市面上的 AI 助手、日历、习惯养成 App 都在替你做决定。Altiora 不替你决定——**它只把每个选择的代价算清楚**，让你自己挑。

## 三段式架构

```
用户说话 → [AI 翻译官] → [计算器（纯 Python）] → [AI 翻译官] → 用户看到代价卡片
         ↑ 理解/抽取      ↑ 永不调用大模型        ↑ 转述成人话
                           同输入 = 同输出
```

## 快速开始

```bash
git clone https://github.com/kinglucky1234/Altiora.luck.git
cd Altiora.luck/Altiora
pip install -r requirements.txt
python server.py
# 浏览器打开 http://localhost:8000
```

**零外部依赖**：Vosk 中文离线语音模型 44MB 已内置，不需要 API Key，断网也能跑。

## 目录结构

```
Altiora.luck/
├── Altiora-未来的我.html      # 单文件原型
├── Altiora-需求文档.docx     # 9 页需求文档
├── Altiora/                  # 桌面版
│   ├── run.bat / run.command
│   ├── server.py
│   └── backend/model/vosk-model-small-cn-0.22/
└── altiora/backend/          # FastAPI 骨架
    ├── calculator.py         # 代价测算核心
    ├── main.py
    ├── schemas.py
    └── translator.py
```
