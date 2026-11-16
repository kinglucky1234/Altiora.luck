"""生成 Altiora 作品介绍文档 PDF。

正文唯一来源是仓库 `docs/Altiora-作品介绍文档.md`，这里只做 Markdown → PDF。
不再手写第二份正文，避免 PDF 与仓库说明两处口径漂移。

依赖 reportlab 与任一中文字体（优先 wqy-microhei，Windows 自动用微软雅黑，找不到会给出安装提示）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md2pdf

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "Altiora-作品介绍文档.md"
OUT = ROOT / "Altiora-作品介绍文档.pdf"

if __name__ == "__main__":
    md2pdf.build(str(SRC), sys.argv[1] if len(sys.argv) > 1 else str(OUT))
