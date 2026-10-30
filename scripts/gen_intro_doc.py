"""生成 Altiora 作品介绍文档 PDF"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

FONT_TTC = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
pdfmetrics.registerFont(TTFont("CJK", FONT_TTC, subfontIndex=0))
pdfmetrics.registerFont(TTFont("CJKB", FONT_TTC, subfontIndex=0))

PRIMARY = HexColor("#1a365d")
ACCENT = HexColor("#2b6cb0")
GRAY = HexColor("#4a5568")
GRID = HexColor("#e2e8f0")

CW = A4[0] - 40*mm

def S(name, **kw):
    base = dict(fontName="CJK", fontSize=11, leading=18, textColor=black,
                wordWrap="CJK", alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

styles = {
    "title": S("t", fontName="CJKB", fontSize=26, leading=36, textColor=PRIMARY,
               alignment=TA_CENTER, spaceAfter=16),
    "sub": S("s", fontSize=13, leading=20, textColor=GRAY, alignment=TA_CENTER, spaceAfter=20),
    "h1": S("h1", fontName="CJKB", fontSize=16, leading=24, textColor=PRIMARY,
            spaceBefore=16, spaceAfter=8),
    "h2": S("h2", fontName="CJKB", fontSize=13, leading=20, textColor=ACCENT,
            spaceBefore=10, spaceAfter=4),
    "body": S("b"),
    "bullet": S("bu", leftIndent=16, bulletIndent=4, spaceAfter=3),
}

story = []
story.append(Paragraph("Altiora.luck 作品介绍文档", styles["title"]))
story.append(Paragraph("—— 更好的自己 · 数字孪生分身 + 代价测算引擎", styles["sub"]))
story.append(Spacer(1, 10))

# (1)
story.append(Paragraph("（1）项目详情及使用方式", styles["h1"]))
story.append(Paragraph("<b>项目名称</b>：Altiora.luck —— 更好的自己数字孪生分身 + 代价测算引擎", styles["body"]))
story.append(Spacer(1, 4))
story.append(Paragraph("<b>项目定位</b>：一款个人效能管理工具。与传统日历 App 只标红冲突不同，Altiora 会把每个选择的代价（金钱、时间、后悔值）算清楚，摆成 A/B/C 三个选项让用户自己选，绝不替用户做决定。", styles["body"]))
story.append(Spacer(1, 4))
story.append(Paragraph("<b>使用方式</b>：", styles["body"]))
for line in [
    "双击 Altiora-未来的我.html 即可运行，无需安装、无需联网（有 API Key 可启用 LLM 润色，无 Key 纯本地确定性运行，功能不减）",
    "首次打开完成 6 步引导问卷（软肋、睡眠、精力高峰、目标、称呼、颜色）",
    "在输入框用自然语言添加日程，如明天 11 点到 1 点家教，时薪 80",
    "冲突时自动弹出 A/B/C 代价卡片，用户自行选择",
    "支持记住…指令写入行为规矩、情绪倾诉只接一句不灌鸡汤、每次对话自动写日记",
]:
    story.append(Paragraph("• " + line, styles["bullet"]))

# (2)
story.append(Paragraph("（2）项目亮点", styles["h1"]))
highlights = [
    ("AI 只做翻译，永不计算", "大模型仅负责自然语言到结构化字段的翻译，所有冲突检测、代价账单、排程均由本地确定性 JS 计算，同一输入永远同一输出。"),
    ("意图控制三层锁", "System Prompt 写死边界 + _BANNED 正则过滤客服腔 + reply=None 强制兜底，模型越不了界。"),
    ("代价可视化", "冲突不喊你应该去，而是摆 A/B/C 三个选项各自的代价（亏多少钱、破不睡底线、事后后悔），把选择权还给用户。"),
    ("档案驱动排程", "精力高峰、睡眠底线、软肋等档案参数直接影响今日方案，改一个参数方案肉眼可见地变，档案不是摆设。"),
    ("三层记忆", "长期记忆（画像）+ 聊天记忆（3 轮滚动）+ 日记（自动摘要），隔 3 天回来会问上次你说的事后来怎么样了。"),
]
for i, (title, desc) in enumerate(highlights, 1):
    story.append(Paragraph(f"<b>{i}. {title}</b>：{desc}", styles["body"]))
    story.append(Spacer(1, 3))

# (3)
story.append(Paragraph("（3）AI 测试技术落地使用情况概述", styles["h1"]))
story.append(Paragraph("<b>AI 在本项目中的角色是翻译官，不是决策者</b>：", styles["body"]))
for line in [
    "自然语言理解：用户输入明天 11 点到 1 点家教，时薪 80，LLM 提取为 intent=schedule, event={name:家教, start:11:00, end:13:00, wage:80}，冲突和代价由本地代码计算。",
    "结果表达：本地计算器算出冲突后，LLM 把确定结果说成一句人话，且只允许引用已有数字，编造数字整句作废。",
    "BYOK 架构：用户自带 API Key，Key 只存浏览器 localStorage，服务端不落盘、不写日志；自填 URL 只允许公网 https，带 DNS 重绑定防护。",
    "确定性兜底：无 Key 或 LLM 调用失败时，全部回退本地规则，功能完整可用。",
    "AI 协同开发：开发过程中使用 Trae 进行 Bug 排查、代码审查、回归用例生成，如以后想正则漏匹配、日记 flush 时机、前导逗号清理等修复均由 AI 协助定位并验证。",
]:
    story.append(Paragraph("• " + line, styles["bullet"]))

# (4)
story.append(Paragraph("（4）项目中涉及的关键技术", styles["h1"]))
tech_data = [
    ["技术", "用途"],
    ["单文件 HTML + 原生 JS", "前端全部逻辑，零构建、零依赖"],
    ["localStorage / IndexedDB", "本地数据持久化，隐私不出浏览器"],
    ["确定性排程算法", "冲突检测、代价计算、精力高峰调度，纯本地"],
    ["FastAPI（Python 3.10+）", "可选后端，LLM 翻译网关"],
    ["LLM 意图控制", "System Prompt + 正则黑名单 + 运行时校验三层锁"],
    ["DNS 重绑定防护", "_safe_base 两层校验（字符串前缀 + DNS 解析查私网 IP）"],
    ["系统 TTS", "免费离线语音朗读"],
]
t = Table(tech_data, colWidths=[CW*0.4, CW*0.6])
t.setStyle(TableStyle([
    ("FONT", (0,0), (-1,-1), "CJK", 10),
    ("FONT", (0,0), (-1,0), "CJKB", 11),
    ("TEXTCOLOR", (0,0), (-1,0), PRIMARY),
    ("BACKGROUND", (0,0), (-1,0), HexColor("#ebf4ff")),
    ("GRID", (0,0), (-1,-1), 0.5, GRID),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(t)

# (5)
story.append(Paragraph("（5）项目相关的图片/照片", styles["h1"]))
story.append(Paragraph("应用截图包括：首页分身球、冲突代价卡片 A/B/C、今日方案、我的画像、日记页、AI 协同 Trae 录屏截图。", styles["body"]))

# (6)
story.append(Paragraph("（6）项目之前是否发表过或获奖", styles["h1"]))
story.append(Paragraph("本项目为首次参加传智杯 B 组·赛道 8 个人效能与赛博具身智能仿真，未在其他场合发表或获奖。", styles["body"]))

# (7)
story.append(Paragraph("（7）若项目是在其他项目基础上优化，请说明优化部分", styles["h1"]))
story.append(Paragraph("本项目为独立开发，非基于已有项目优化。开发过程中参考了日历类应用的冲突标红机制，但核心设计（代价 A/B/C 选项、AI 只翻译不决策、档案驱动排程）均为原创。", styles["body"]))

doc = SimpleDocTemplate("/workspace/Altiora-作品介绍文档.pdf", pagesize=A4,
                        leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm)
doc.build(story)
print("PDF 生成完成：Altiora-作品介绍文档.pdf")
