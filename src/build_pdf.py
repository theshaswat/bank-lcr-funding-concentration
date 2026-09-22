"""
Markdown -> PDF renderer for reports/*.md and README.md, using reportlab
Platypus.

Covers only the markdown subset these documents use: headings, tables,
bold/italic, horizontal rules and bullet lists.

Usage: python3 build_pdf.py
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)

from config import ROOT, REPORTS_DIR

ACCENT = colors.HexColor("#1F2A44")   # navy, matches the charts
LGREY = colors.HexColor("#F2F2F2")
DGREY = colors.HexColor("#6B7280")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16,
                          textColor=ACCENT, spaceBefore=2, spaceAfter=6,
                          fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("H1Sub", parent=styles["Normal"], fontSize=9.5,
                          textColor=DGREY, fontName="Helvetica-Oblique",
                          spaceAfter=10, keepWithNext=1))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12.5,
                          textColor=ACCENT, spaceBefore=11, spaceAfter=5,
                          fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11,
                          textColor=ACCENT, spaceBefore=8, spaceAfter=4,
                          fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.3,
                          leading=12.4, spaceAfter=5, alignment=TA_LEFT,
                          allowWidows=0, allowOrphans=0))
styles.add(ParagraphStyle("BodyBold", parent=styles["Body"],
                          fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("BulletItem", parent=styles["Body"], leftIndent=14,
                          bulletIndent=4, spaceAfter=3))
styles.add(ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.3,
                          leading=10.6, alignment=TA_LEFT))
styles.add(ParagraphStyle("CellHead", parent=styles["Cell"],
                          fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle("Small", parent=styles["Normal"], fontSize=8,
                          textColor=DGREY, fontName="Helvetica-Oblique",
                          spaceAfter=6, leading=11))
styles.add(ParagraphStyle("Quote", parent=styles["Body"], leftIndent=12,
                          textColor=DGREY, fontName="Helvetica-Oblique",
                          borderColor=DGREY, spaceAfter=8))
styles.add(ParagraphStyle("CodeBlock", parent=styles["Normal"], fontName="Courier",
                          fontSize=7.6, leading=10.2, textColor=ACCENT))


# Base Helvetica has no glyph for these and reportlab substitutes a
# lookalike instead of erroring, so map them to ASCII before rendering.
# The rupee sign is the one this project actually uses throughout its
# reports — Helvetica has no glyph for it either, so it becomes "Rs".
UNICODE_SAFE = {
    "→": "->",
    "≈": "~",
    "×": " x ",
    "–": "-",
    "—": " - ",
    "−": "-",
    "‑": "-",
    "’": "'", "‘": "'", '"': '"', '"': '"',
    "…": "...",
    "₹": "Rs ",
    # box-drawing chars used in the README's folder-tree fence — Courier
    # has no glyph for these either, so give the tree ASCII equivalents.
    "├": "+", "└": "+", "─": "-", "│": "|", "┬": "+", "┴": "+", "┼": "+",
}


def inline(text):
    """Markdown inline -> reportlab mini-XML. Order matters: bold before italic."""
    # External links stay clickable; relative repo paths render as plain
    # text, since a standalone PDF can't resolve them.
    def _link_sub(m):
        label, href = m.group(1), m.group(2)
        if href.startswith(("http://", "https://")):
            return f"\x00LINKSTART\x00{href}\x00LINKMID\x00{label}\x00LINKEND\x00"
        return label
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link_sub, text)

    for bad, good in UNICODE_SAFE.items():
        text = text.replace(bad, good)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\s{2,}", " ", text)  # cleanup from " x "/" Rs " substitution

    def _restore_link(m):
        href, label = m.group(1), m.group(2)
        return f'<link href="{href}" color="#1F2A44"><u>{label}</u></link>'
    text = re.sub(r"\x00LINKSTART\x00(.*?)\x00LINKMID\x00(.*?)\x00LINKEND\x00",
                  _restore_link, text)
    return text


def code_block(lines, avail_width):
    """Render a fenced code block as monospace text in a shaded box,
    preserving line breaks and indentation — inline() would strip both
    and misread '**'/backticks inside a tree diagram or shell command."""
    esc_lines = []
    for line in lines:
        t = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for bad, good in UNICODE_SAFE.items():
            t = t.replace(bad, good)
        leading = len(line) - len(line.lstrip(" "))
        t = "&nbsp;" * leading + t.lstrip(" ") if leading else t
        esc_lines.append(t if t.strip() else "&nbsp;")
    para = Paragraph("<br/>".join(esc_lines) or "&nbsp;", styles["CodeBlock"])
    tbl = Table([[para]], colWidths=[avail_width - 18])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LGREY),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ]))
    return tbl


def parse_table(lines, i):
    """Parse a GFM table starting at lines[i]. Returns (rows, next_index)."""
    rows = []
    header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    rows.append(header)
    i += 2  # skip header + separator
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(row)
        i += 1
    return rows, i


def make_table(rows, avail_width):
    # A blank or near-blank markdown header row would render as an empty
    # filled bar, so drop it and treat the rest as data.
    if rows and all(not c.strip() for c in rows[0]):
        rows = rows[1:]
        has_header = False
    elif rows and sum(1 for c in rows[0] if c.strip()) == 1 and len(rows[0]) > 1:
        has_header = False
    else:
        has_header = True
    if not rows:
        return Spacer(1, 0)

    ncols = len(rows[0])
    body_start = 1 if has_header else 0
    # Right-align columns whose header or majority of data cells look numeric.
    def is_numeric_col(c):
        vals = [rows[r][c] for r in range(body_start, len(rows)) if c < len(rows[r])]
        hits = sum(1 for v in vals if re.match(r"^[\$\-\(]?[\d,\.]+[%\)]?x?$|^[+\-]?[\d,\.]+%?$", v.replace(",", "").replace(" ", "")) or v in ("—", "-", ""))
        return hits >= max(1, len(vals) * 0.6)

    numeric_cols = [is_numeric_col(c) for c in range(ncols)]
    first_col_width = min(avail_width * 0.32, 2.5 * inch)
    remaining = avail_width - first_col_width
    other_width = remaining / max(1, ncols - 1)
    col_widths = [first_col_width] + [other_width] * (ncols - 1)

    data = []
    for r, row in enumerate(rows):
        cells = []
        for c in range(ncols):
            val = row[c] if c < len(row) else ""
            style = styles["CellHead"] if (has_header and r == 0) else styles["Cell"]
            p = Paragraph(inline(val), style)
            cells.append(p)
        data.append(cells)

    for row_paras in data:
        for p in row_paras:
            p.style.leading = p.style.fontSize + 1.6
    t = Table(data, colWidths=col_widths, repeatRows=1 if has_header else 0)
    ts = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if has_header:
        ts += [
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    first_body = 1 if has_header else 0
    for r in range(first_body, len(data)):
        if (r - first_body) % 2 == 1:
            ts.append(("BACKGROUND", (0, r), (-1, r), LGREY))
        # bold rows: a row whose first cell is bold-marked in source (**...**)
        if rows[r][0].strip().startswith("**"):
            ts.append(("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"))
    for c in range(ncols):
        if numeric_cols[c] and c > 0:
            ts.append(("ALIGN", (c, first_body), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(ts))
    return t


def build_story(md_text, avail_width):
    lines = md_text.split("\n")
    story = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(inline(stripped[4:]), styles["H3"]))
            i += 1
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(inline(stripped[3:]), styles["H2"]))
            i += 1
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(inline(stripped[2:]), styles["H1"]))
            i += 1
            continue

        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            story.append(Spacer(1, 2))
            story.append(KeepTogether([code_block(buf, avail_width)]))
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            story.append(Paragraph(inline(" ".join(buf)), styles["Quote"]))
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("---") and set(stripped) <= {"-"}:
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.6,
                                    color=colors.HexColor("#D9D9D9")))
            story.append(Spacer(1, 8))
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:\-\|]+\|?$", lines[i + 1].strip()):
            rows, i = parse_table(lines, i)
            tbl = make_table(rows, avail_width)
            # Keep a table whole rather than letting it straddle a page break.
            story.append(Spacer(1, 2))
            story.append(KeepTogether([tbl]))
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**") and stripped.count("*") == 2:
            story.append(Paragraph(inline(stripped[1:-1]), styles["Small"]))
            i += 1
            continue

        if re.match(r"^(\d+\.|[-*])\s+", stripped):
            marker = re.match(r"^(\d+\.|[-*])\s+", stripped).group(1)
            buf = [re.sub(r"^(\d+\.|[-*])\s+", "", stripped)]
            i += 1
            # Absorb continuation lines so a wrapped bullet stays one item.
            while i < n and lines[i].strip() and not (
                lines[i].strip().startswith(("#", "|"))
                or re.match(r"^(\d+\.|[-*])\s+", lines[i].strip())
            ):
                buf.append(lines[i].strip())
                i += 1
            bullet_text = " ".join(buf)
            # U+2022 has no glyph in base Helvetica; use an ASCII marker.
            bullet_char = marker if marker[0].isdigit() else "-"
            story.append(Paragraph(f"{bullet_char}&nbsp;&nbsp;{inline(bullet_text)}",
                                   styles["BulletItem"]))
            continue

        # Paragraph: accumulate to the next blank or structural line. The
        # trailing space in the list pattern matters -- it stops a line that
        # merely opens with "**bold**" from being read as a bullet.
        buf = [stripped]
        i += 1
        while i < n and lines[i].strip() and not (
            lines[i].strip().startswith(("#", "|"))
            or re.match(r"^(\d+\.|[-*])\s+", lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        text = " ".join(buf)
        story.append(Paragraph(inline(text), styles["Body"]))

    return story


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9D9D9"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 0.45 * inch,
                LETTER[0] - doc.rightMargin, 0.45 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(DGREY)
    canvas.drawString(doc.leftMargin, 0.30 * inch, doc.title)
    canvas.drawRightString(LETTER[0] - doc.rightMargin, 0.30 * inch,
                           f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def render(md_path, pdf_path, title):
    text = Path(md_path).read_text()
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=LETTER,
        topMargin=0.55 * inch, bottomMargin=0.62 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        title=title,
    )
    avail_width = LETTER[0] - doc.leftMargin - doc.rightMargin
    story = build_story(text, avail_width)
    n_flowables = len(story)  # build() consumes the list
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"Wrote {pdf_path}  ({n_flowables} flowables, {doc.page} page(s))",
          file=sys.stderr)


def main():
    # Only the memo and the README get a PDF twin — the reader-facing
    # documents someone would open standalone. DATA_DICTIONARY.md and
    # LIMITATIONS.md are reference material, meant to be browsed on GitHub
    # alongside the code they document, not printed.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    render(REPORTS_DIR / "liquidity_risk_memo.md", REPORTS_DIR / "liquidity_risk_memo.pdf",
           "Bank LCR & Funding Concentration — Liquidity Risk Memo")
    render(ROOT / "README.md", REPORTS_DIR / "README.pdf",
           "Bank LCR & Funding Concentration — Project Overview")


if __name__ == "__main__":
    main()
