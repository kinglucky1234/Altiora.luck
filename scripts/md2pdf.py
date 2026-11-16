"""极简 Markdown → PDF（支持标题/段落/列表/表格/代码块/粗体/图片）"""
import os, re, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]


def register_cjk_fonts():
    """按平台依次尝试中文字体；都没有就明确报错，而不是抛一堆 traceback。"""
    for path in FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            pdfmetrics.registerFont(TTFont("CJK", path, subfontIndex=0))
            pdfmetrics.registerFont(TTFont("CJKB", path, subfontIndex=0))
            return
        except Exception:
            continue
    raise SystemExit(
        "未找到可用的中文字体。\n"
        "  Linux:   sudo apt install fonts-wqy-microhei\n"
        "  macOS:   安装任意中文字体（如 PingFang / 思源黑体）\n"
        "  Windows: 确认 C:/Windows/Fonts/msyh.ttc 存在（系统自带微软雅黑）\n"
        "也可以把字体绝对路径加到 FONT_CANDIDATES 列表里。"
    )


register_cjk_fonts()

PRIMARY = HexColor("#1a365d")
ACCENT = HexColor("#2b6cb0")
GRAY = HexColor("#4a5568")
GRID = HexColor("#cbd5e0")
LIGHT = HexColor("#ebf4ff")

CW = A4[0] - 40 * mm


def st(name, **kw):
    base = dict(fontName="CJK", fontSize=10.5, leading=17, textColor=black,
                wordWrap="CJK", alignment=TA_JUSTIFY, spaceAfter=6)
    base.update(kw)
    return ParagraphStyle(name, **base)


S = {
    "title": st("title", fontName="CJKB", fontSize=20, leading=30, textColor=PRIMARY,
                alignment=TA_CENTER, spaceBefore=0, spaceAfter=14),
    "h1": st("h1", fontName="CJKB", fontSize=17, leading=25, textColor=PRIMARY, spaceBefore=14, spaceAfter=8),
    "h2": st("h2", fontName="CJKB", fontSize=13, leading=20, textColor=ACCENT, spaceBefore=10, spaceAfter=5),
    "h3": st("h3", fontName="CJKB", fontSize=11.5, leading=18, textColor=PRIMARY, spaceBefore=8, spaceAfter=4),
    "body": st("b"),
    "quote": st("q", textColor=GRAY, leftIndent=10, fontSize=9.5, leading=15),
    "bullet": st("bu", leftIndent=16, bulletIndent=4, spaceAfter=2),
    "code": st("code", fontName="CJK", fontSize=8.2, leading=13, textColor=HexColor("#e2e8f0"),
               backColor=HexColor("#1e293b"), leftIndent=6, rightIndent=6, spaceBefore=3, spaceAfter=6),
    "cell": st("cell", fontSize=9, leading=14, spaceAfter=0),
    "cellh": st("cellh", fontName="CJKB", fontSize=9.5, leading=14, textColor=PRIMARY, spaceAfter=0),
    "cap": st("cap", fontSize=9, leading=14, textColor=GRAY, alignment=TA_CENTER,
              spaceBefore=2, spaceAfter=10),
}

IMG_RE = re.compile(r"^!\[(.*?)\]\((.+?)\)(?:\{width=([\d.]+)in\})?$")


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<font color='#2b6cb0'>\1</font>", t)
    return t


def build(md_path, pdf_path):
    lines = open(md_path, encoding="utf-8").read().splitlines()
    base_dir = os.path.dirname(os.path.abspath(md_path))
    story, i, in_code, code_buf = [], 0, False, []
    seen_title = False
    max_h = A4[1] - 40 * mm

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if s.startswith("```"):
            if in_code:
                story.append(Paragraph("<br/>".join(x.replace(" ", "&nbsp;") for x in code_buf), S["code"]))
                code_buf, in_code = [], False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(ln)
            i += 1
            continue

        if not s:
            i += 1
            continue
        img = IMG_RE.match(s)
        if img:
            path = img.group(2)
            if not os.path.isabs(path):
                path = os.path.join(base_dir, path)
            if os.path.exists(path):
                from PIL import Image as PILImage
                iw, ih = PILImage.open(path).size
                w = float(img.group(3)) * 72 if img.group(3) else CW
                w = min(w, CW)
                h = ih * w / iw
                if h > max_h:
                    h, w = max_h, iw * max_h / ih
                # 单图不超过版心高度的 45%，保证一页能放两张，避免半页空白
                cap = max_h * 0.45
                if h > cap:
                    h, w = cap, iw * cap / ih
                story.append(Image(path, width=w, height=h))
            else:
                story.append(Paragraph(inline(s), S["body"]))
        elif s.startswith("图 ") and "·" in s:
            story.append(Paragraph(inline(s), S["cap"]))
        elif s.startswith("# "):
            style = S["h1"] if seen_title else S["title"]
            seen_title = True
            story.append(Paragraph(inline(s[2:]), style))
        elif s.startswith("## "):
            story.append(Paragraph(inline(s[3:]), S["h2"]))
        elif s.startswith("### "):
            story.append(Paragraph(inline(s[4:]), S["h3"]))
        elif s.startswith(">"):
            story.append(Paragraph(inline(s.lstrip("> ").strip()), S["quote"]))
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                data = [[Paragraph(inline(c), S["cellh"] if r == 0 else S["cell"]) for c in row] for r, row in enumerate(rows)]
                ncol = max(len(r) for r in rows)
                tbl = Table(data, colWidths=[CW / ncol] * ncol, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, GRID),
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 8))
            continue
        elif s.startswith(("- ", "* ")):
            story.append(Paragraph("• " + inline(s[2:]), S["bullet"]))
        elif re.match(r"^\d+\.\s", s):
            story.append(Paragraph(s[:s.index(".")] + "." + inline(s[s.index(".") + 1:]), S["bullet"]))
        elif s == "---":
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(inline(s), S["body"]))
        i += 1

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm)
    doc.build(story)
    print("generated:", pdf_path)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
