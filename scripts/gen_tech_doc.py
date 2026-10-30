"""
生成 Altiora 技术文档 PDF（≤30 页）
重点：意图控制策略 / 架构设计 / 可复现性论证 / AI 协同演进链路
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted, KeepTogether, Flowable,
)

# ── 字体：用 wqy-microhei.ttc（TrueType 轮廓，reportlab 支持）──
FONT_TTC = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
pdfmetrics.registerFont(TTFont("CJK", FONT_TTC, subfontIndex=0))
pdfmetrics.registerFont(TTFont("CJKB", FONT_TTC, subfontIndex=0))
CJK = "CJK"
CJKB = "CJKB"

# ── 颜色 ──
PRIMARY = HexColor("#1a365d")
ACCENT = HexColor("#2b6cb0")
LIGHT = HexColor("#ebf4ff")
GRAY = HexColor("#4a5568")
CODEBG = HexColor("#1e293b")
CODEFG = HexColor("#e2e8f0")
GRID = HexColor("#e2e8f0")

# ── 页面常量 ──
PAGE_W, PAGE_H = A4
LM = RM = 20 * mm
TM = BM = 18 * mm
CW = PAGE_W - LM - RM

# ── 样式 ──
def S(name, **kw):
    base = dict(fontName=CJK, fontSize=10.5, leading=17, textColor=black,
                wordWrap="CJK", alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

styles = {
    "cover_title": S("ct", fontName=CJKB, fontSize=30, leading=40,
                     textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=10),
    "cover_sub": S("cs", fontSize=14, leading=22, textColor=GRAY,
                   alignment=TA_CENTER, spaceAfter=6),
    "h1": S("h1", fontName=CJKB, fontSize=18, leading=26, textColor=PRIMARY,
            spaceBefore=18, spaceAfter=8),
    "h2": S("h2", fontName=CJKB, fontSize=14, leading=20, textColor=ACCENT,
            spaceBefore=14, spaceAfter=6),
    "h3": S("h3", fontName=CJKB, fontSize=11.5, leading=17, textColor=PRIMARY,
            spaceBefore=10, spaceAfter=4),
    "body": S("body"),
    "body_sm": S("bs", fontSize=9.5, leading=15),
    "bullet": S("bu", leftIndent=14, bulletIndent=2, spaceAfter=3),
    "code": S("code", fontName=CJK, fontSize=8.5, leading=12,
              textColor=CODEFG, backColor=CODEBG, leftIndent=6, rightIndent=6,
              spaceBefore=4, spaceAfter=4, wordWrap="CJK"),
    "caption": S("cap", fontSize=9, leading=13, textColor=GRAY,
                 alignment=TA_CENTER, spaceBefore=4, spaceAfter=10),
}

class Divider(Flowable):
    def __init__(self, w, h=1.5, color=ACCENT, sb=4, sa=8):
        super().__init__(); self.w=w; self.hh=h; self.c=color
        self.spaceBefore=sb; self.spaceAfter=sa
    def draw(self):
        self.canv.setFillColor(self.c)
        self.canv.rect(0,0,self.w,self.hh,fill=1,stroke=0)

def H1(t): return [Paragraph(t, styles["h1"]), Divider(CW*0.25)]
def H2(t): return [Paragraph(t, styles["h2"])]
def H3(t): return [Paragraph(t, styles["h3"])]
def P(t): return Paragraph(t, styles["body"])
def PS(t): return Paragraph(t, styles["body_sm"])
def B(t): return Paragraph("• " + t, styles["bullet"])
def CAP(t): return Paragraph(t, styles["caption"])
def CODE(t):
    return Preformatted(t, styles["code"])

def TBL(data, col_w=None, header=True):
    t = Table(data, colWidths=col_w, repeatRows=1 if header else 0)
    style = [
        ("FONTNAME", (0,0), (-1,-1), CJK),
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("ALIGN", (0,1), (-1,-1), "LEFT"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), 0.5, GRID),
    ]
    if header:
        style += [
            ("BACKGROUND", (0,0), (-1,0), PRIMARY),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONTNAME", (0,0), (-1,0), CJKB),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, HexColor("#f7fafc")]),
        ]
    t.setStyle(TableStyle(style))
    return t

story = []

# ════════════════════════════════════════
# 封面
# ════════════════════════════════════════
story.append(Spacer(1, 40*mm))
story.append(Paragraph("Altiora · 未来的我", styles["cover_title"]))
story.append(Paragraph("数字孪生分身 + 代价测算引擎", styles["cover_sub"]))
story.append(Spacer(1, 6*mm))
story.append(Divider(60*mm, 2, ACCENT, sb=2, sa=10))
story.append(Paragraph("技术文档", styles["cover_sub"]))
story.append(Spacer(1, 30*mm))
story.append(Paragraph("全国高校 Vibe Coding 开发挑战赛 · B 组", styles["cover_sub"]))
story.append(Paragraph("赛道 8：个人效能与赛博具身智能仿真", styles["cover_sub"]))
story.append(Spacer(1, 15*mm))
story.append(Paragraph("提交日期：2026 年 12 月", styles["body_sm"]))
story.append(PageBreak())

# ════════════════════════════════════════
# 目录
# ════════════════════════════════════════
story += H1("目录")
toc = [
    ["章节", "内容"],
    ["1", "作品概述"],
    ["2", "需求分析"],
    ["3", "架构设计"],
    ["4", "意图控制策略（重点）"],
    ["5", "核心功能与确定性逻辑"],
    ["6", "AI 协同与演进链路（重点）"],
    ["7", "工程质量与安全"],
    ["8", "测试方案与结果"],
    ["9", "可复现性论证"],
    ["10", "创新点小结"],
    ["11", "部署方案"],
    ["12", "不足与展望"],
]
story.append(TBL(toc, [15*mm, 145*mm]))
story.append(PageBreak())

# ════════════════════════════════════════
# 1. 作品概述
# ════════════════════════════════════════
story += H1("1. 作品概述")
story += H2("1.1 一句话定位")
story.append(P("市面上的 AI 助手、日历、习惯养成 App 都在<b>替用户做决定</b>。Altiora 不替你决定——它只把每个选择的代价算清楚，让你自己挑。核心是一个「数字孪生分身」：基于用户的日常数据（目标、软肋、睡眠硬约束、规矩），在浏览器内实时测算每个日程决策的代价。"))
story += H2("1.2 时代背景与产业需求")
story.append(P("2026 年，自然语言已成为新一代的编程语言。Vibe Coding 从极客调侃演变为企业快速验证 MVP 与敏捷开发的主流手段，代码编写成本趋近于零，<b>定义问题、产品设计、系统架构编排以及指挥 AI 的能力</b>成为核心竞争力。产业界对「超级个体（Solo Developer）」的需求，正是本作品的出发点——一个人 + AI，在几小时内交付一套完整可用、可复现的系统。"))
story += H2("1.3 解决的痛点")
story.append(B("现有助手替用户做选择，用户失去掌控感，完成率一掉就想「重开」。"))
story.append(B("日程冲突只有「哪件更重要」的粗暴排序，没有「代价」视角，用户无法预判损失。"))
story.append(B("AI 生成内容不可信：模型会编时间、编数字、给鸡汤，用户无法信任排程结果。"))
story.append(B("档案变摆设：很多产品的「设置」参数并不真正影响后续行为，用户填了等于没填。"))
story += H2("1.4 核心创新")
story.append(P("<b>代价账单代替记分板</b>：冲突时给出 A/B/C 三个选项，每个选项的得与失（金钱、时间、睡眠、后悔值）都摆出来，不替用户选。"))
story.append(P("<b>LLM 只做翻译，不做计算</b>：所有时间差、金钱、冲突分钟数由本地确定性代码算出，LLM 只把自然语言翻成结构化字段、把结果说成人话。"))
story.append(P("<b>档案不是摆设</b>：精力高峰、睡眠硬约束、软肋、目标都真实影响排程——改一个参数，今日方案肉眼可见地变。"))

story += H2("1.5 与赛题契合度")
story.append(P("赛道 8「个人效能与赛博具身智能仿真」要求基于用户日常数据快速搭建数字孪生分身，支持自适应日程冲突调整。本作品的契合点："))
story.append(B("<b>数字孪生分身</b>：档案（目标/软肋/睡眠硬约束/规矩/精力高峰）即用户的数字孪生，真实驱动排程决策。"))
story.append(B("<b>自适应日程冲突</b>：冲突检测 + 代价账单 + 今日方案重排，全部由本地确定性逻辑自适应计算。"))
story.append(B("<b>前端精致动效</b>：单 HTML 内嵌时间轴、冲突卡片、记忆卡等交互动效，双击即可体验。"))
story.append(B("<b>Vibe Coding 范式</b>：由 Solo Developer 指挥 AI 完成，全过程有细粒度 Git 记录与 Prompt 快照可复现。"))

# ════════════════════════════════════════
# 2. 需求分析
# ════════════════════════════════════════
story += H1("2. 需求分析")
story += H2("2.1 目标用户")
story.append(P("高校学生与职场新人——日程密集、目标模糊、容易被 AI 助手的「鸡汤」和「替你决定」带偏。他们需要的不是又一个待办清单，而是一个能把<b>决策代价</b>算清楚的参谋。"))
story += H2("2.2 核心使用场景")
sc_tbl = [
    ["场景", "用户行为", "系统响应"],
    ["冲突决策", "「周五下午3点家教和组会撞了」", "给出 A/B/C 三选项及代价，让用户自己挑"],
    ["目标规划", "「我想考上研究生」", "抽取为长期目标，写入档案，影响后续排程优先级"],
    ["精力优化", "改档案精力高峰为 14:00–17:00", "今日方案把脑力活挪进高峰窗"],
    ["久别重逢", "3 天以上没打开", "翻日记：「上次你说要考试，后来怎么样了？」"],
    ["情绪接住", "「今天没睡好」", "一句话接住情绪，不出表格不灌鸡汤"],
]
story.append(TBL(sc_tbl, [22*mm, 55*mm, 83*mm]))
story.append(CAP("表 2-1 核心使用场景"))
story += H2("2.3 功能需求清单")
story.append(PS("按 P0/P1/P2 分层（来自迭代 2 的 AI 协同决策）："))
story.append(B("<b>P0</b>：日程输入、冲突检测、代价账单（A/B/C）、删除与重算"))
story.append(B("<b>P1</b>：长期目标抽取与记忆、精力高峰驱动的今日方案排程、记忆三层（长期/聊天/日记）"))
story.append(B("<b>P2</b>：语音输入（Vosk 离线）、语音输出（系统 TTS）、AI 在线模式（BYOK）"))
story += H2("2.4 非功能需求")
story.append(B("<b>可复现</b>：同一输入永远同一输出，排程逻辑不依赖 LLM。"))
story.append(B("<b>数据安全</b>：Key 只存浏览器，服务端不落盘；自填 URL 防内网探测。"))
story.append(B("<b>离线可用</b>：双击 HTML 即可用全部文字功能，不依赖网络。"))
story.append(B("<b>优雅降级</b>：无 Key 或 Key 失效时，所有功能依然完整，只是文案偏机械。"))

# ════════════════════════════════════════
# 3. 架构设计
# ════════════════════════════════════════
story += H1("3. 架构设计")
story.append(P("赛题要求阐述「AI 生成的代码采用了什么架构，你如何约束它」。本作品采用<b>三段式混合驱动架构</b>，核心约束是：<b>第二段（计算器）不含任何概率成分</b>，同一输入永远同一输出。这是用户能信任它的唯一理由，也是可复现性的根基。"))

story += H2("3.1 三段式架构")
arch_tbl = [
    ["阶段", "职责", "是否调用 LLM"],
    ["① AI 翻译官", "自然语言 → 结构化字段（意图/事件/记忆/目标/情绪）", "是，失败自动退回本地规则"],
    ["② 计算器", "冲突检测、代价账单、今日方案排程", "否，纯确定性代码"],
    ["③ AI 表达", "把情绪与计算结果说成人话", "是，失败回退确定性文案"],
]
story.append(TBL(arch_tbl, [25*mm, 85*mm, 50*mm]))
story.append(CAP("表 3-1 三段式架构"))
story.append(P("三段之间<b>只通过结构化数据传递</b>，LLM 永远不接触数字计算。计算器的输出（facts）是 AI 表达的唯一输入，且表达层有数字校验防止编造。"))

story += H2("3.2 前后端职责划分")
story.append(P("<b>前端（单 HTML 文件）</b>：所有状态、记忆、排程、冲突计算都在浏览器内完成。双击 HTML 即可用文字与 AI，不需要 Python。后端仅提供两个可选能力——语音识别（Vosk 离线模型）和可选的 LLM 代理。不存用户数据，不写 Key 日志。"))

story += H2("3.3 数据流")
story.append(P("用户输入 → LLM 翻译（directUnderstand）→ 结构化字段 → 本地计算器（detectConflicts / buildTodayPlan）→ 结果 facts → LLM 表达（directSay）→ 展示。整个链路中，<b>LLM 永远不接触数字计算</b>，数字只在计算器里产生，在表达层被校验。"))

story += H2("3.4 关键设计原则")
story.append(B("<b>LLM 边界写死在代码里</b>：intent 不是 emotion/chat 时，模型生成的 reply 被直接丢弃。"))
story.append(B("<b>没说结束时间就追问</b>：event 为 null 时不替用户编时间，宁可问一句。"))
story.append(B("<b>双模式自动切换</b>：无 Key 走本地规则，有 Key 走 AI 在线，功能都完整。"))
story.append(B("<b>BYOK（自带 Key）</b>：Key 只存浏览器 localStorage，请求由浏览器直连厂商，服务端不落盘。"))
story.append(B("<b>确定性的归确定性，生成的归生成</b>：排程由本地规则算，LLM 只负责把结果说成人话；LLM 失败一律回退确定性文案。"))

story += H2("3.5 AI 生成代码的约束策略")
story.append(P("如何约束 AI 生成的代码不跑偏，是 Vibe Coding 的核心问题。本作品采用四层约束："))
story.append(B("<b>角色约束（SYSTEM Prompt）</b>：从输入侧告诉模型只能做翻译，不能计算、不能决策。"))
story.append(B("<b>字段约束（JSON Schema 思维）</b>：LLM 输出必须是固定结构（intent/event/memory/goal/social/reply），缺字段或类型错直接判失败。"))
story.append(B("<b>运行时校验</b>：reply 丢弃、数字校验、_BANNED 正则，三层运行时拦截。"))
story.append(B("<b>回退约束</b>：任何校验失败都回退本地确定性逻辑，保证功能不中断。"))

# ════════════════════════════════════════
# 4. 意图控制策略（重点）
# ════════════════════════════════════════
story += H1("4. 意图控制策略")
story.append(P("这是本作品的核心，权重 20%。我们用<b>三层锁</b>把 LLM 锁在「翻译官」的角色里，防止它越界做计算、做决策、说鸡汤。每一层都有实战 Bug 佐证其必要性。"))

story += H2("4.1 三层锁总览")
lock_tbl = [
    ["层级", "机制", "作用", "实现位置"],
    ["第一层", "SYSTEM Prompt 边界", "从输入侧告诉模型能做什么、不能做什么", "llm.py SYSTEM / 前端 LLM_SYS"],
    ["第二层", "_BANNED 正则", "过滤客服腔和鸡汤句", "llm.py _BANNED / 前端 LLM_BANNED"],
    ["第三层", "reply 丢弃 + 数字校验", "schedule/safety 场景强制丢弃 reply；say 阶段数字必须来自 facts", "llm.py understand() / 前端 directUnderstand / directSay"],
]
story.append(TBL(lock_tbl, [18*mm, 40*mm, 60*mm, 42*mm]))
story.append(CAP("表 4-1 意图控制三层锁"))

story += H2("4.2 第一层：SYSTEM Prompt 边界")
story.append(P("SYSTEM prompt 明确列出 7 种意图（safety/emotion/schedule/memory/goal/social/chat），并对每种 intent 的 event/memory/goal/social 字段做了抽取规则。最关键的是「绝对不能做」清单："))
story.append(CODE("""【绝对不能做】
- 不计算时间重叠、时长、金钱、代价
- 不替用户选方案，不说「你应该选 A」
- 不编造用户没说的地点、时间、人物
- 不说「加油」「你可以的」「相信自己」，不喊口号
- 不复述用户原话，不用客服腔"""))
story.append(P("reply 的写法也被严格约束：intent=schedule 且 event 完整时 reply 必须为 null（账还没算，不能抢答）；intent=safety 时 reply 为 null（前端有固定安全话术）。"))

story += H2("4.3 第二层：_BANNED 正则过滤")
story.append(P("即使 SYSTEM prompt 写了禁止，模型仍可能输出客服腔。所以在代码层加了一道正则，命中即作废。前后端各有一份完全相同的正则，因为 LLM 调用有两条路径：浏览器直连（directUnderstand）和服务端代理（understand），两条路径都要过滤。"))
story.append(CODE("""_BANNED = re.compile(
    r"嗯[，,]\\s*我在听|我在听|你接着说|我在这儿|我都在|"
    r"会好起来的|会好一点|加油|你可以的|相信自己|"
    r"慢慢来|不要放弃|你能做到"
)
# 命中 → reply = None，前端用本地兜底话术"""))

story += H2("4.4 第三层：reply 丢弃 + 数字校验")
story += H3("4.4.1 schedule/safety 场景强制丢弃 reply")
story.append(P("完整日程的账必须由计算器算完再说，LLM 不能抢答。安全场景由前端固定话术处理，不让模型自由发挥。"))
story.append(CODE("""# 服务端 llm.py
if intent in ("safety",) or (intent == "schedule" and event):
    reply = None

# 前端 directUnderstand（同样逻辑，双保险）
if intent == "safety" or (intent == "schedule" and event):
    reply = None"""))

story += H3("4.4.2 say 阶段数字校验")
story.append(P("第二段翻译官（directSay / say）把计算器的结果说成人话。为防止模型编造数字，我们校验：输出中出现的所有数字，必须是 facts 里已有的数字，多一个就整句作废。"))
story.append(CODE("""# 前端 directSay
const allowed = new Set((JSON.stringify(facts).match(/\\d+(?:\\.\\d+)?/g) || []));
const nums = text.match(/\\d+(?:\\.\\d+)?/g) || [];
if (nums.some(n => !allowed.has(n))) return "";  // 编造数字 → 作废"""))
story.append(P("服务端 say() 同样实现了数字集合校验（_numbers 函数），双路径一致。"))

story += H2("4.5 失败回退机制")
story.append(P("任何一层校验失败，都不会让用户看到空白或错误——而是回退到<b>本地确定性文案</b>。"))
story.append(B("directUnderstand 返回 null → 前端用 parseEventsFromText 本地解析，或追问时间。"))
story.append(B("directSay 返回空 → 前端用拼好的确定性文案（如「『考研复习 14:00-16:00』加进时间轴了，没冲突」）。"))
story.append(B("explainPlan 失败 → 用 planCaption() 拼一句说清「为什么这么排」。"))
story.append(P("核心原则：<b>LLM 是锦上添花，不是功能前提</b>。没有 Key 或 Key 失效，所有功能依然完整可用。"))

story += H2("4.6 实战 Bug 佐证：「LLM 忽略档案」")
story.append(P("这是三层锁设计的直接动因。现象：模型拿到「昨日方案」后，输出一句通用套话，完全没提精力高峰时段，也没提档案里的睡眠底线/软肋——档案变摆设。"))
story += H3("根因")
story.append(B("Prompt 只说了「解释方案」，没强制要求引用档案字段；"))
story.append(B("输出没有任何运行时校验，说漏了也直接展示。"))
story += H3("修复（双保险）")
story.append(B("<b>Prompt 层</b>：把「必须明确说出哪件事被排进了哪个精力高峰时段」写成铁律；"))
story.append(B("<b>代码层</b>（explainPlan）：精力高峰一旦填写，校验输出必须包含时段字符串或被挪事项名，任一不满足 → 丢弃 LLM 输出 → 回退 planCaption()。"))
story += H3("回归验证")
story.append(CODE("""LLM 输出「我把考研复习排到 14:00–17:00，因为你这段精神最好」
  → 命中时段「14:00–17:00」 → 通过
LLM 输出「今天排得很满，你自己注意休息」
  → 未命中 → 回退确定性文案"""))
story.append(P("这个 Bug 的完整调试过程记录在 PROMPT_LOG.md 与 AI协同对话历史.md 中。"))

story += H2("4.7 Prompt 上下文设计详解")
story.append(P("比赛要求阐述「如何设计上下文和 Prompt」。本作品的上下文设计遵循「<b>只给事实，不给结论</b>」原则——把档案和输入的事实结构化地喂给 LLM，让它做翻译，不做推理。"))

story += H3("4.7.1 directUnderstand 的报文构造")
story.append(P("意图识别阶段，user 报文由两部分组成：档案摘要 + 用户原话。档案摘要 profileBrief 只包含计算器需要的字段（目标、软肋、睡眠硬约束、精力高峰、规矩），不包含冗余信息，避免模型分心。"))
story.append(CODE("""# user 报文结构
档案：
{profileBrief(DATA.profile)}

用户原话：
{text}

请按 SYSTEM 规则抽取结构化字段。"""))
story.append(P("设计要点：档案在前、原话在后，让模型先建立「用户是谁」的上下文，再理解当前输入。字段清单与 SYSTEM 中定义的 intent 类型一一对应。"))

story += H3("4.7.2 explainPlan 的报文构造")
story.append(P("今日方案说明阶段，user 报文包含档案摘要 + 方案事实 planFacts（JSON）。planFacts 只包含计算器已算出的事实（哪些事被挪、挪到哪、冲突情况、睡眠底线是否保住），LLM 只需把这些事实说成一两句话。"))
story.append(CODE("""# user 报文结构
档案：
{profileBrief(DATA.profile)}

方案（只解释，不改）：
{JSON.stringify(planFacts)}"""))
story.append(P("设计要点：planFacts 是 JSON，数字已确定，LLM 无法编造（4.4.2 数字校验兜底）。「只解释，不改」明确告诉模型这是翻译任务，不是决策任务。"))

story += H3("4.7.3 directSay 的报文构造")
story.append(P("情绪与结果表达阶段，user 报文包含 intent + 结构化 facts。模型根据 intent 选择语气（emotion 共情、schedule 中性陈述），facts 中的数字是唯一允许出现的数字。"))

story += H2("4.8 完整 SYSTEM Prompt（节选）")
story.append(P("以下为前端 LLM_SYS 的核心节选，展示意图分类与字段抽取规则。完整版本见 Altiora-未来的我.html 的 LLM_SYS 常量。"))
story.append(CODE("""你是 Altiora，一个只做「自然语言 → 结构化字段」翻译的助手。

【意图分类】只能输出以下 7 种 intent 之一：
  safety   — 自伤/极端情绪，触发安全话术
  emotion  — 情绪宣泄，只共情不给建议
  schedule — 日程安排，抽取 event
  memory   — 要记住某事，抽取 memory
  goal     — 长期目标，抽取 goal
  social   — 社交场合建议，抽取 social
  chat     — 闲聊

【绝对不能做】
- 不计算时间重叠、时长、金钱、代价
- 不替用户选方案
- 不编造用户没说的地点、时间、人物
- 不说鸡汤、不喊口号

【reply 规则】
- intent=schedule 且 event 完整 → reply 必须为 null
- intent=safety → reply 必须为 null
- 其他 intent 可写一句简短人话

输出 JSON：{"intent":..., "event":..., "memory":..., "goal":..., "social":..., "reply":...}"""))

# ════════════════════════════════════════
# 5. 核心功能与确定性逻辑
# ════════════════════════════════════════
story += H1("5. 核心功能与确定性逻辑")

story += H2("5.1 冲突检测与代价账单")
story.append(P("detectConflicts 遍历同一天的事件两两比较，重叠分钟数 > 0 即为冲突。makeConflict 为每对冲突生成 A/B/C 三个选项："))
cf_tbl = [
    ["选项", "含义", "代价示例"],
    ["A", "去优先级高的那件", "损失家教 2 小时 × 80 元 = 160 元"],
    ["B", "去优先级低的那件", "放弃重要的事，事后可能后悔"],
    ["C", "把低优先级的顺延", "连轴转，可能破睡眠硬约束"],
]
story.append(TBL(cf_tbl, [15*mm, 55*mm, 90*mm]))
story.append(CAP("表 5-1 冲突代价账单三选项"))
story += H3("detectConflicts 核心逻辑")
story.append(P("遍历同一天事件两两比较，计算重叠分钟数。重叠 > 0 即冲突。核心是时间区间重叠判定："))
story.append(CODE("""# 两事件 [s1,e1] 与 [s2,e2] 重叠判定
overlap = min(e1, e2) - max(s1, s2)
if overlap > 0:
    conflict = makeConflict(a, b, overlap)
# makeConflict 按优先级决定 hi/lo：
#   A = 去 hi，代价 = lo 的 wage × dur(lo)
#   B = 去 lo，代价 = 定性「放弃重要的事」
#   C = lo 顺延到 hi.end + 30min，检查是否破睡眠底线"""))
story.append(P("注意：makeConflict 里的金钱计算（wage × dur）、优先级判断、顺延时间（hi.end + 30 分钟）全部是本地计算，LLM 完全不参与。这是「LLM 只做翻译」原则的直接体现。"))

story += H2("5.2 今日方案排程（buildTodayPlan）")
story.append(P("这是「档案不是摆设」的核心证明。规则："))
story.append(B("课程/会议/睡眠 = 固定项，原地不动；学习/兼职 = 可动项。"))
story.append(B("可动项按「优先级小者先 → 时长长的先」排序。"))
story.append(B("在精力高峰时间窗内贪心塞入，撞到固定项就绕过，塞不下保持原位。"))
story.append(P("改档案里的 preferred_focus_hours，方案肉眼可见地变："))
story.append(CODE("""档案精力高峰 = "14:00–17:00"
  → 「考研复习」从 15:00-17:00 挪到 14:00-16:00（moved=true）

档案精力高峰 = "08:00–11:00"（此时 08:30-10:10 有课占窗）
  → 「考研复习」保持原位（moved=false）

档案精力高峰 = 未填
  → 方案按原时间排，不优化"""))
story += H3("focusWindowOf 与贪心塞入逻辑")
story.append(P("排程算法确定性的核心：先求可塞入的时间窗，再按固定顺序贪心塞入。"))
story.append(CODE("""# focusWindowOf：从 preferred_focus_hours 中扣除固定项占用，
#   得到剩余可塞入的连续子窗
window = peak_hours
for fixed in fixed_events:
    window = window - fixed   # 区间减法

# buildTodayPlan：按「优先级升序 → 时长降序」排序可动项，
#   从窗头开始塞，撞到固定项就跳过，塞不下保持原位
for task in sorted(movable, key=lambda t: (t.priority, -t.dur)):
    if fits(window_head, task.dur):
        place(task, window_head)
        window_head += task.dur
    else:
        keep_original(task)   # 不动，不报错"""))
story.append(P("算法复杂度 O(n log n)（排序主导），无递归、无随机、无 LLM 调用。同一组事件 + 同一档案永远产出同一方案。"))

story += H2("5.3 记忆三层")
mem_tbl = [
    ["层", "存什么", "保留多久", "谁用"],
    ["长期记忆 (profile)", "目标、软肋、睡眠硬约束、规矩", "一直", "计算器输入，只有明说才写"],
    ["聊天记忆", "最近 3 轮对话原文", "超 6 条滚掉", "只接半句（「就那个」「三点」）"],
    ["日记", "每行「日期：摘要」", "最多 180 行", "隔 3 天以上回来才翻"],
]
story.append(TBL(mem_tbl, [30*mm, 50*mm, 30*mm, 50*mm]))
story.append(CAP("表 5-2 记忆三层设计"))
story.append(P("三层各管各的，用「保留时长」划边界，避免记多了像监视、记少了每句从零开始。日记按「目标 → 排了什么 → 那会儿的状态」拼摘要，不存原话。"))

story += H2("5.4 目标抽取（extractGoal 七步规则）")
story.append(P("这是意图控制在「字段抽取」层面的体现。用户说「你好啊，我想当科学家」，存进去的应该是「成为科学家」而不是原话。七步规则："))
story.append(B("① 剥寒暄（去掉问候、语气词）"))
story.append(B("② 锚点词截断（我想/我要/我希望/我的目标是/我以后想 等）"))
story.append(B("③ 去时间/连接词（明天、以后、而且）"))
story.append(B("④ 动词归一（当/做 → 成为）"))
story.append(B("⑤ 去语气词（啊、呢、吧）"))
story.append(B("⑥ 长度护栏（过长则截断）"))
story.append(B("⑦ 情绪/当天事挡在门外（我想哭、我明天想去图书馆 → 不存）"))
story.append(P("修复前曾出现「我以后想成为科学家」解析失败的 Bug——M 正则缺「我以后想」，而 goalHorizon 判定长期的关键词里却有「以后想」，两头不一致。修复后两者关键词完全对齐。"))

# ════════════════════════════════════════
# 6. AI 协同与演进链路（重点）
# ════════════════════════════════════════
story += H1("6. AI 协同与演进链路")
story.append(P("本章节对应评分维度「过程可复现性与演进链路」（25%）与「方法创新性与意图控制」（20%）。记录与 AI 协作的真实过程，证明作品不是一次性拼接，而是逐步迭代演进。完整对话历史见 AI协同对话历史.md 与 prompt-snapshots/。"))

story += H2("6.1 协同方法论")
story.append(P("与 AI 协作的核心原则是：<b>我负责定义问题与验证，AI 负责产出与建议</b>。每一轮遵循「我提 Prompt → AI 给方案 → 我判断并要求实测 → 验证通过才落地」。AI 的产出不直接合入，必须经过本地断言或浏览器实测验证。"))
story.append(P("混合驱动架构的选型决策也是与 AI 对话得出：纯 LLM 不可复现、纯规则生硬，采用「确定性排程 + LLM 装饰」分离，互不污染。"))

story += H2("6.2 六个核心迭代")
iter_tbl = [
    ["迭代", "主题", "关键决策"],
    ["1", "目标规划 + 自适应重规划", "闭环：目标→计划→执行→状态→重规划；重规划由本地确定性逻辑驱动"],
    ["2", "功能分层 + 记忆库选型", "P0/P1/P2 分层；放弃复杂数据库，用 localStorage 轻量记忆"],
    ["3", "产品表现形式", "单 HTML 原型先行，左输入右时间轴，2 分 25 秒出可交互原型"],
    ["4", "LLM 配置面板 + 语音", "BYOK（Key 只存浏览器）+ DNS 重绑定防护；系统 TTS 免费离线"],
    ["5", "修 Bug：目标存成整句", "extractGoal 拆检测与抽取两步，七步规则，7 正例 + 2 反例全过"],
    ["6", "记忆分三层", "长期/聊天/日记，保留时长划边界，3 天以上翻日记回访"],
]
story.append(TBL(iter_tbl, [12*mm, 45*mm, 103*mm]))
story.append(CAP("表 6-1 六个核心迭代（完整 Prompt 链见 AI协同对话历史.md）"))
story.append(P("每轮迭代的完整 Prompt 原文、AI 输出、决策与截图索引，均记录在 AI协同对话历史.md 中，覆盖远超比赛要求的「≥3 个核心功能迭代完整 Prompt 链」。以下选取迭代 5 与迭代 6 展开，展示「我提 Prompt → AI 给方案 → 我要求实测 → 验证通过才落地」的完整协作链路。"))

story += H3("6.2.1 迭代 5 详解：目标抽取七步规则")
story.append(P("<b>我的 Prompt</b>：「有个 bug，我输入『你好啊，我想当科学家』，直接把原话放进长期目标了。只留目标本身：上面那句最后存的应该是『成为科学家』，不是原话。语言逻辑是什么样子的」"))
story.append(P("<b>AI 输出</b>：把「检测」和「抽取」拆成两步，重写 extractGoal()——剥寒暄 → 锚点词截断 → 去时间/连接词 → 动词归一 → 去语气词 → 长度护栏 → 情绪/当天事挡在门外。"))
story.append(P("<b>实测对照表（7 正例 + 2 反例）</b>："))
goal_test = [
    ["输入", "抽取结果", "说明"],
    ["我想当科学家", "成为科学家", "当→成为"],
    ["我想成为科学家", "成为科学家", "已是成为"],
    ["我想做老师", "成为老师", "做→成为"],
    ["我的目标是考上研究生", "考上研究生", "判断词剥离"],
    ["我希望减肥成功", "减肥成功", "希望类锚点"],
    ["我打算学编程", "学编程", "打算类锚点"],
    ["我以后想成为科学家", "成为科学家", "以后想锚点 + 去时间词"],
    ["我想哭", "（不存）", "情绪，挡在门外"],
    ["我明天想去图书馆", "（不存）", "当天事，挡在门外"],
]
story.append(TBL(goal_test, [50*mm, 40*mm, 70*mm]))
story.append(CAP("表 6-2 extractGoal 实测对照（9 例全过）"))
story.append(P("<b>决策</b>：9 例全过才提交。这一步把「检测关键词」和「抽取内容」彻底分离，避免了「检测用 A 词、存进去用原话」的 Bug。"))

story += H3("6.2.2 迭代 6 详解：记忆三层")
story.append(P("<b>我的 Prompt</b>：「做记忆分层，分成长期记忆和聊天记忆和日记。长期记忆要符合软件优势，聊天记忆短一点主要是上下文不太突兀。日记主要是每次聊完存一行『日期：摘要』，平时不掺和，超过 3 天没来，翻日记上次你说要考试，后来怎么样了」"))
story.append(P("<b>AI 设计判断</b>：记多了像监视，记少了每句从零开始。三层用「保留时长」划边界，各管各的。"))
story.append(P("<b>实测数据</b>："))
story.append(CODE("""输入：「我要考试」→ 追问时间 → 「明天下午三点到五点」
  → 补成事件 15:00-17:00  ✓
聊完 5 轮后：聊天记忆稳定 6 条  ✓
日记落成：10月24日：想成为科学家，排了考试 15:00-17:00，那会儿很累  ✓
把日期调到 4 天前重开：
  开场即「上次（10月20日）你说想成为科学家，后来怎么样了？」  ✓"""))
story.append(P("<b>决策</b>：日记不存原话，只存「目标→排了什么→状态」摘要，既保护隐私又能在久别重逢时唤起上下文。聊天记忆只接半句（「就那个」「三点」），不参与长期决策。"))

story += H2("6.3 实战 Bug 修复合集")
story.append(P("以下为提交前打磨阶段与 AI 协作排查的 5 个真实 Bug，每条均含「现象 → 根因 → 修复 → 回归」。"))

story += H3("Bug A：规矩带前导逗号")
story.append(B("<b>现象</b>：「记住，我晚上容易刷手机」→ 画像显示 `，我晚上容易刷手机`。"))
story.append(B("<b>根因</b>：本地规矩提取截断后未清理首尾标点。"))
story.append(B("<b>修复</b>：新增 stripPunct() 去首尾 CJK/ASCII 标点，在 cleanMemory() 与两条本地提取路径套用。"))
story.append(B("<b>回归</b>：画像页不再出现前导标点。"))

story += H3("Bug B：「我以后想成为科学家」解析失败")
story.append(B("<b>现象</b>：extractGoal 返回空，去掉「以后」就正常；讽刺的是 goalHorizon 里「以后想」是判定 long 的关键词，提取函数却先挂了。"))
story.append(B("<b>根因</b>：extractGoal 的 M 正则缺「我以后想/以后想」（因为「我想」要求紧邻），提取与判定关键词不一致。"))
story.append(B("<b>修复</b>：M 正则补「我以后想/以后想/我以后要/以后要」；goalHorizon 同步补「以后要」。"))
story.append(B("<b>回归</b>：返回「成为科学家」/「long」。"))

story += H3("Bug C：日记层看不见（5 分钟才 flush）")
story.append(B("<b>现象</b>：设完目标后日记页要等 5 分钟空闲才落一条，演示时摸不到「久别重逢」卖点。"))
story.append(B("<b>根因</b>：sessFlush() 只在 idle 定时器触发，无主动触发点。"))
story.append(B("<b>修复</b>：sessFlush() 在设目标（LLM + 本地）和 addStructuredEvent() 后立即调用；空闲阈值 5min→60s；日记页渲染自动日记 + 久别重逢预览。"))
story.append(B("<b>回归</b>：设完目标立即落日记。"))

story += H3("Bug D：LLM 缺字段导致整页崩溃")
story.append(B("<b>现象</b>：LLM 返回缺 start/end 的事件，或 localStorage 加载损坏数据时，toMin(undefined) 抛 TypeError，整页白屏。"))
story.append(B("<b>根因</b>：toMin、addStructuredEvent、日记渲染对脏数据无守卫。"))
story.append(B("<b>修复</b>：toMin 加 typeof 检查 + includes(\":\") 守卫；addStructuredEvent 设默认值；加载时 filter 校验；日记 e.s.split() 加存在性判断。"))
story.append(B("<b>回归</b>：脏数据不再崩溃。"))

story += H3("Bug E：extractGoal 前导冒号 + 判断词「是」残留")
story.append(B("<b>现象</b>：「我想：成为科学家」→ `：成为科学家`；「我的目标是：成为科学家」→ `是：成为科学家`。"))
story.append(B("<b>根因</b>：与 Bug A 同病根——截断后标点没刮干净，且判断词「是」未剥离。"))
story.append(B("<b>修复</b>：判断词「是」加进剥离列表，归一后统一 stripPunct。"))
story.append(B("<b>回归</b>：9 个用例全过，正常 case 结果不变。"))

# ════════════════════════════════════════
# 7. 工程质量与安全
# ════════════════════════════════════════
story += H1("7. 工程质量与安全")

story += H2("7.1 DNS 重绑定防护")
story.append(P("用户自填的 LLM Base URL 可能被用来探测内网。我们做了两层防护："))
story.append(B("<b>第一层</b>：字符串前缀过滤，挡掉 localhost、127.x、10.x、192.168.x 等。"))
story.append(B("<b>第二层</b>：DNS 解析后逐一检查返回 IP，若落在私网/回环/保留范围则拒绝（防 DNS 重绑定）。"))
story.append(CODE("""def _safe_base(base):
    u = urlparse(base)
    if u.scheme != "https" or not u.hostname: return False
    # 第一层：字符串前缀
    if any(h == p or h.startswith(p) for p in _PRIVATE_HOSTS): return False
    # 第二层：DNS 解析后查 IP
    infos = socket.getaddrinfo(h, u.port or 443, type=socket.SOCK_STREAM)
    for info in infos:
        if _is_private_ip(info[4][0]): return False
    return True"""))

story += H2("7.2 BYOK 安全设计")
story.append(B("Key 只存浏览器 localStorage，服务端不落盘、不写日志、不进仓库。"))
story.append(B("请求由浏览器直连厂商 API，不经过服务端中转。"))
story.append(B("服务端 .env 模式仅用于单人自用；开放给他人时强制 BYOK。"))

story += H2("7.3 输入校验")
story.append(B("event 必须有 name + 合法 start/end（HH:MM），否则丢弃。"))
story.append(B("时间区间必须 end > start，否则 event = null。"))
story.append(B("所有字段有长度上限（name ≤20，memory ≤60，goal ≤60）。"))
story.append(B("extra_headers 做头注入防护：过滤 Host/Content-Length 等危险头，限制长度。"))

story += H2("7.4 单文件可维护性")
story.append(P("前端为单 HTML 文件，便于部署与评审。为避免「AI 生成的单文件不可维护」问题，代码按功能分区（意图识别/计算器/记忆/表达/渲染），三区通过结构化数据耦合，LLM 相关代码集中在 directUnderstand/directSay/explainPlan 三个函数，修改 LLM 行为不会影响确定性计算。"))

story += H2("7.5 性能与无死循环论证")
story.append(P("评审维度要求「无严重安全漏洞与性能死循环」。本作品所有计算路径均有明确上界："))
story.append(B("<b>冲突检测</b>：两两比较 O(n²)，n 为单日事件数（通常 <20），常数级耗时。"))
story.append(B("<b>排程贪心</b>：排序 O(n log n) + 线性塞入 O(n)，单次生成今日方案 <1ms。"))
story.append(B("<b>记忆滚窗</b>：聊天记忆超 6 条即 shift 掉最早一条，数组长度恒定；日记最多 180 行，超限截断。"))
story.append(B("<b>无递归</b>：所有循环均为有界 for/while，不存在递归调用栈溢出风险。"))
story.append(B("<b>LLM 超时</b>：directUnderstand/directSay 均设 fetch 超时（默认 15s），超时即回退确定性文案，不会挂起界面。"))

# ════════════════════════════════════════
# 8. 测试方案与结果
# ════════════════════════════════════════
story += H1("8. 测试方案与结果")
test_tbl = [
    ["#", "操作", "预期结果", "实际结果"],
    ["1", "说「今天没睡好」", "AI 用一句话接住情绪，不出表格", "通过"],
    ["2", "「我明天下午要和导师讨论」", "听懂意图但时间不全 → 追问，不编时间", "通过"],
    ["3", "「周五下午3点到5点去家教」", "抽成事件排进时间轴，算出冲突与代价", "通过"],
    ["4", "「记住，我晚上容易刷手机」", "写入画像，冲突时代价栏出现", "通过"],
    ["5", "改精力高峰为 14:00–17:00，生成今日方案", "可动脑力活被挪进高峰窗", "通过"],
    ["6", "配自己的 LLM Key", "AI 在线模式，理解更准", "通过"],
    ["7", "删除日程", "hover 出 ×，点击删除，冲突重算", "通过"],
    ["8", "「我以后想成为科学家」", "目标存为「成为科学家」，长期", "通过"],
    ["9", "3 天以上未打开", "开场翻日记回访", "通过"],
]
story.append(TBL(test_tbl, [8*mm, 50*mm, 62*mm, 20*mm]))
story.append(CAP("表 8-1 核心链路测试用例与结果"))

story += H2("8.1 确定性断言测试")
story.append(P("排程核心（focusWindowOf / buildTodayPlan / planCaption）脱离浏览器环境单独断言，同一输入永远同一输出："))
story.append(CODE("""精力高峰 = "14:00–17:00" → 考研复习挪到 14:00-16:00  ✓
精力高峰 = "08:00–11:00"（被课占）→ 不动                  ✓
精力高峰 = 未填 → 不优化                                    ✓
ALL PASS ✓"""))

story += H2("8.2 意图控制回归测试")
story.append(P("extractGoal 抽取 9 个用例全过，含正例与反例；explainPlan 数字校验对编造数字的输出正确作废；_BANNED 对客服腔正确拦截。"))

story += H2("8.3 意图控制三层锁专项测试")
ic_tbl = [
    ["层级", "测试输入", "预期行为", "结果"],
    ["第一层 SYSTEM", "「帮我算一下这两件事哪个更重要」", "intent=schedule，reply=null，不替用户选", "通过"],
    ["第二层 _BANNED", "用户情绪低，LLM 输出「加油你可以的」", "命中 _BANNED → reply 作废 → 回退", "通过"],
    ["第三层 reply 丢弃", "「明天下午3点到5点家教」", "event 完整 → reply 强制 null，等计算器", "通过"],
    ["第三层 数字校验", "facts 含 14:00，LLM 输出「15:00」", "15 不在 facts 数字集合 → 整句作废", "通过"],
    ["第三层 数字校验", "facts 含 160 元，LLM 输出「160 元」", "160 在 facts → 通过", "通过"],
    ["回退机制", "LLM 超时无响应", "directSay 返回空 → 用 planCaption 兜底", "通过"],
]
story.append(TBL(ic_tbl, [28*mm, 50*mm, 55*mm, 20*mm]))
story.append(CAP("表 8-2 意图控制三层锁专项测试"))

# ════════════════════════════════════════
# 9. 可复现性论证
# ════════════════════════════════════════
story += H1("9. 可复现性论证")
story.append(P("评审标准中「过程可复现性与演进链路」占 25%。我们从四个维度保证可复现。"))

story += H2("9.1 细粒度 Git 提交历史")
story.append(P("禁止「initial commit 包含全部功能」。每次提交对应一次与 AI 的核心对话或一个功能模块的落地。近期提交示例："))
git_tbl = [
    ["提交哈希", "说明"],
    ["ccbc732", "fix: 规矩前导逗号 + 「我以后想」解析 + 日记 flush"],
    ["51eb90b", "fix: LLM 事件缺字段/损坏数据/日记健壮性修复"],
    ["5d13f0c", "fix(goal): extractGoal 前导冒号/判断词「是」残留"],
    ["a332469", "fix(frontend): LLM 没抽出 event 时用本地时间解析兜底"],
    ["6c504f0", "fix(frontend): tryFillPending 别在用户说了日期时拿旧日期乱填"],
    ["991f6e9", "chore: 技术文档 PDF 与视频脚本移出仓库（单独提交网盘）"],
]
story.append(TBL(git_tbl, [25*mm, 135*mm]))
story.append(CAP("表 9-1 细粒度提交示例（完整历史见 git log）"))

story += H2("9.2 Prompt 历史快照")
story.append(P("prompt-snapshots/ 目录保存了 6 个核心功能迭代的完整对话链截图，每个都包含「用户提问 → AI 输出 → 决策/实测」。AI协同对话历史.md 提供可检索的文字版。远超比赛要求的「≥3 个核心功能迭代完整 Prompt 链」。"))
shot_tbl = [
    ["截图文件", "迭代", "内容"],
    ["iter1-01-goal-discussion.png", "1", "完整对话链，用户先开口"],
    ["iter1-02-goal-loop-design.png", "1", "AI 提出闭环，用户追问"],
    ["iter1-03-adaptive-replan.png", "1", "确定「自适应」是赛题关键词"],
    ["iter2-01-layered-design.png", "2", "按「自适应程度」分层功能"],
    ["iter2-02-memory-vs-framework.png", "2", "为什么不搞复杂数据库"],
    ["iter3-01-form-explained.png", "3", "通俗版产品描述"],
    ["iter3-02-final-preview.png", "3", "2 分 25 秒出可交互原型"],
    ["iter4-01-llm-config-panel.png", "4", "配置面板字段与安全验证"],
    ["iter4-02-local-tts.png", "4", "确定用系统自带 TTS"],
    ["iter5-01-goal-extraction.png", "5", "七步抽取规则与实测对照表"],
    ["iter6-01-memory-layers.png", "6", "三层记忆表格与实测结果"],
]
story.append(TBL(shot_tbl, [55*mm, 12*mm, 93*mm]))
story.append(CAP("表 9-2 Prompt 快照清单（共 11 张，覆盖 6 个迭代）"))

story += H2("9.3 自检脚本")
story.append(P("自检.py 提供十项检查：Python 版本、四个依赖、语音模型完整性、前端关键控件、页面无真实 API Key、服务启动、识别接口连通。不联网、不调大模型、不消耗额度。全过退出码 0。"))

story += H2("9.4 确定性断言")
story.append(P("排程核心可脱离浏览器环境单独断言。同一输入永远同一输出，证明排程逻辑完全确定、可复现。详见 8.1 节。"))

# ════════════════════════════════════════
# 10. 创新点小结
# ════════════════════════════════════════
story += H1("10. 创新点小结")
story.append(B("<b>代价账单代替记分板</b>：冲突不替用户选，而是把 A/B/C 的代价（金钱/时间/睡眠/后悔）摆出来。"))
story.append(B("<b>LLM 只做翻译不做计算</b>：确定性排程与 LLM 表达分离，数字只在计算器产生、在表达层校验，可复现且可信。"))
story.append(B("<b>三层意图控制锁</b>：SYSTEM + _BANNED + reply 丢弃/数字校验，配合失败回退，把 LLM 锁死在翻译官角色。"))
story.append(B("<b>档案不是摆设</b>：精力高峰、睡眠硬约束、软肋真实影响排程，改一个参数方案肉眼可见地变。"))
story.append(B("<b>记忆三层 + 久别重逢</b>：长期/聊天/日记用保留时长划边界，3 天以上回访日记，既不监视又不冷漠。"))
story.append(B("<b>BYOK + DNS 重绑定防护</b>：Key 只存浏览器，自填 URL 双层校验防内网探测。"))

# ════════════════════════════════════════
# 11. 部署方案
# ════════════════════════════════════════
story += H1("11. 部署方案")
story += H2("11.1 零依赖模式（推荐评委使用）")
story.append(P("双击 Altiora-未来的我.html 即可。文字对话、排程、冲突代价、记忆、今日方案全部在前端完成，不需要 Python、不需要联网。"))

story += H2("11.2 语音模式")
story.append(P("<b>环境要求</b>：Python 3.10 及以上（代码使用了 `str | None` / `list[dict]` 等类型注解）。"))
story.append(CODE("""pip install -r requirements.txt
python3 scripts/download_vosk.py    # 仅首次，下载语音模型
python server.py                     # 启动后打开 http://localhost:8000"""))

story += H2("11.3 AI 在线模式")
story.append(P("页面右上角点状态标签 → 填自己的 API Key → 保存。Key 只存本机浏览器，请求直连厂商。支持 DeepSeek / 通义 / 火山方舟等 OpenAI 兼容接口。"))

# ════════════════════════════════════════
# 12. 不足与展望
# ════════════════════════════════════════
story += H1("12. 不足与展望")
story += H2("12.1 当前不足")
story.append(B("目标抽取依赖正则锚点词，对复杂句式（如「要是能...就好了」）覆盖有限，未来可引入轻量意图分类模型。"))
story.append(B("代价账单的「后悔值」目前是定性描述，未量化，说服力有限。"))
story.append(B("记忆三层均为本地存储，换设备需手动导出导入，暂无云端同步。"))
story.append(B("单 HTML 文件虽便于部署，但代码量增长后可维护性下降，未来可拆分为模块化工程。"))

story += H2("12.2 未来展望")
story.append(B("引入用户行为反馈（实际完成/未完成），让分身根据真实执行情况动态调整排程策略。"))
story.append(B("代价量化：把睡眠债、后悔值等抽象代价转成可比较的分数，辅助决策。"))
story.append(B("多分身对比：同一目标下生成多种排程风格的分身，用户可对比选择。"))
story.append(B("端到端加密的记忆同步，在保护隐私前提下支持跨设备。"))

story.append(Spacer(1, 10*mm))
story.append(Divider(CW*0.4, 1, GRAY, sb=10, sa=6))
story.append(Paragraph("—— 全文完 ——", styles["caption"]))

# ── 生成 ──
out = "/workspace/Altiora-技术文档.pdf"
doc = SimpleDocTemplate(out, pagesize=A4,
    leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
    title="Altiora 技术文档", author="Altiora")
doc.build(story)
print("OK:", out)
