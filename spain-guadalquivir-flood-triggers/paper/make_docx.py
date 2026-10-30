"""Word versions of the paper and the technical report, for editing (MIT licence).

Run after build_documents.py:  python paper/make_docx.py paper/
Converts paper.html and technical_report.html with pandoc, then tidies the result with python-docx:
A4 with 2 cm margins, Times New Roman body, Arial headings, full-width tables, figures at text width,
page numbers in the footer.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BODY, HEAD = "Times New Roman", "Arial"
BLUE = RGBColor(0x1F, 0x3B, 0x73)


def set_font(style, name, size=None, bold=None, italic=None, color=None):
    f = style.font
    f.name = name
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(k), name)
    for k in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rf.get(qn(k)) is not None:
            del rf.attrib[qn(k)]
    if size: f.size = Pt(size)
    if bold is not None: f.bold = bold
    if italic is not None: f.italic = italic
    if color is not None: f.color.rgb = color


def reference_doc(path: Path) -> None:
    subprocess.run(["pandoc", "-o", str(path), "--print-default-data-file", "reference.docx"], check=True)
    d = Document(path)
    st = {s.name: s for s in d.styles}
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text"):
        if name in st:
            set_font(st[name], BODY, 11)
            pf = st[name].paragraph_format; pf.space_after = Pt(6); pf.line_spacing = 1.15
            if name == "Compact": pf.space_after = Pt(2)
    for name, size in (("Title", 18), ("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11.5), ("Heading 4", 11)):
        if name in st:
            set_font(st[name], HEAD, size, bold=True, italic=False, color=BLUE)
            st[name].paragraph_format.space_before = Pt(12 if name != "Heading 1" else 6); st[name].paragraph_format.space_after = Pt(4)
            st[name].paragraph_format.keep_with_next = True
    for name in ("Image Caption", "Table Caption", "Caption"):
        if name in st:
            set_font(st[name], HEAD, 9, bold=False, italic=False, color=RGBColor(0x33, 0x33, 0x33))
    d.save(path)


def borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge, sz in (("top", 8), ("bottom", 8), ("insideH", 2)):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), "9AA7BD"); b.append(e)
    for edge in ("left", "right", "insideV"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "nil"); b.append(e)
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None: tblPr.remove(old)
    tblPr.append(b)
    w = tblPr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW"); tblPr.append(w)
    w.set(qn("w:type"), "pct"); w.set(qn("w:w"), "5000")
    lay = tblPr.find(qn("w:tblLayout"))
    if lay is not None: tblPr.remove(lay)


def tidy(docx_path: Path) -> None:
    d = Document(docx_path)
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.0); sec.top_margin = sec.bottom_margin = Cm(2.0)
    text_w = sec.page_width - sec.left_margin - sec.right_margin
    # tables: full width, small type, header bold, no row split
    for t in d.tables:
        borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, row in enumerate(t.rows):
            trPr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
            if i == 0:
                th = OxmlElement("w:tblHeader"); trPr.append(th)
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(0); p.paragraph_format.space_before = Pt(1); p.paragraph_format.line_spacing = 1.0
                    for r in p.runs:
                        r.font.size = Pt(8); r.font.name = HEAD
                        if i == 0: r.font.bold = True
    # figures at text width (narrow charts at 70 %)
    for shp in d.inline_shapes:
        w, h = shp.width, shp.height
        if not w: continue
        ratio = h / w
        target = text_w if ratio < 0.62 else int(text_w * 0.72)
        shp.width = target; shp.height = int(target * ratio)
    for p in d.paragraphs:
        if p._p.xpath(".//w:drawing"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
    # page numbers
    fp = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = txt
        run._r.append(el)
    run.font.size = Pt(9); run.font.name = HEAD
    d.save(docx_path)


def convert(html: Path, out: Path, ref: Path) -> None:
    src = html.read_text(encoding="utf-8")
    src = re.sub(r"<title>.*?</title>", "", src, flags=re.S)          # no pandoc title block; the h1 is the title
    src = re.sub(r'<div class="cover-line"></div>', "", src)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(src); tmp = f.name
    subprocess.run(["pandoc", tmp, "-f", "html", "-t", "docx", "--reference-doc", str(ref), "-o", str(out)], check=True)
    Path(tmp).unlink()
    tidy(out)


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    ref = folder / "_reference.docx"
    reference_doc(ref)
    for name in ("paper", "technical_report"):
        convert(folder / f"{name}.html", folder / f"{name}.docx", ref)
        print("wrote", folder / f"{name}.docx")
    ref.unlink()


if __name__ == "__main__":
    main()
