"""Render OPERATING_MANUAL.md into a polished, printable PDF with ReportLab.

Usage (from repo root, with the backend venv that has reportlab):
    backend/venv/Scripts/python tools/build_manual.py [--shop "Shop Name"]

Output: OPERATING_MANUAL.pdf
"""
import argparse
import html
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, ListFlowable, ListItem, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
ACCENT = colors.HexColor('#2f6df0')
INK = colors.HexColor('#1e2640')
MUTED = colors.HexColor('#5b6781')

# Emoji / symbols that the PDF core fonts can't render -> plain text.
REPLACE = {
    '🔔': 'Bell -', '👤': 'Profile -', '✓': 'tick', '💵': '', '💳': '',
    '📋': '', '🤖': '', '⚠️': 'Note:', '→': '->', '½': '1/2',
    '—': ' - ', '–': '-', '₹': 'Rs ', '“': '"', '”': '"', '‘': "'", '’': "'",
    '×': 'x', '≤': '<=', '≥': '>=', '•': '-',
}


def inline(text: str) -> str:
    for k, v in REPLACE.items():
        text = text.replace(k, v)
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`(.+?)`', r'<font face="Courier" size="9">\1</font>', text)
    text = re.sub(r'\[(.+?)\]\([^)]+\)', r'\1', text)  # links -> text
    # Drop any remaining non-latin-1 chars so nothing renders as a box.
    return text.encode('latin-1', 'ignore').decode('latin-1')


def styles():
    s = getSampleStyleSheet()
    return {
        'h1': ParagraphStyle('h1', parent=s['Heading1'], fontSize=17, spaceBefore=14,
                             spaceAfter=6, textColor=INK),
        'h2': ParagraphStyle('h2', parent=s['Heading2'], fontSize=13.5, spaceBefore=12,
                             spaceAfter=4, textColor=ACCENT),
        'h3': ParagraphStyle('h3', parent=s['Heading3'], fontSize=11.5, spaceBefore=8,
                             spaceAfter=2, textColor=INK),
        'body': ParagraphStyle('body', parent=s['BodyText'], fontSize=10, leading=14,
                               spaceAfter=4),
        'li': ParagraphStyle('li', parent=s['BodyText'], fontSize=10, leading=13.5),
        'quote': ParagraphStyle('quote', parent=s['BodyText'], fontSize=9.5, leading=13,
                                textColor=MUTED, leftIndent=8, backColor=colors.HexColor('#f4f7fc'),
                                borderPadding=6, spaceBefore=4, spaceAfter=6),
        'cell': ParagraphStyle('cell', parent=s['BodyText'], fontSize=9, leading=12),
        'cellh': ParagraphStyle('cellh', parent=s['BodyText'], fontSize=9, leading=12,
                                textColor=colors.white, fontName='Helvetica-Bold'),
    }


def build(shop: str):
    md = (ROOT / 'OPERATING_MANUAL.md').read_text(encoding='utf-8').splitlines()
    st = styles()
    flow = []

    # --- Title page ---
    flow += [
        Spacer(1, 60 * mm),
        Paragraph(shop, ParagraphStyle('shop', fontSize=24, alignment=TA_CENTER,
                                       textColor=INK, spaceAfter=6, fontName='Helvetica-Bold')),
        Paragraph('PharmaDesk', ParagraphStyle('pd', fontSize=16, alignment=TA_CENTER,
                                               textColor=ACCENT, spaceAfter=20)),
        HRFlowable(width='50%', color=colors.HexColor('#d7deeb'), spaceAfter=20),
        Paragraph('OPERATING MANUAL', ParagraphStyle('t', fontSize=20, alignment=TA_CENTER,
                                                     textColor=INK, fontName='Helvetica-Bold')),
        Spacer(1, 10 * mm),
        Paragraph('Pharmacy Inventory, Billing &amp; Supply-Chain Software',
                  ParagraphStyle('sub', fontSize=11, alignment=TA_CENTER, textColor=MUTED)),
        Spacer(1, 40 * mm),
        Paragraph(f'Issued: {date.today():%d %B %Y}',
                  ParagraphStyle('d', fontSize=10, alignment=TA_CENTER, textColor=MUTED)),
        Paragraph('Keep this manual at the counter.',
                  ParagraphStyle('d2', fontSize=10, alignment=TA_CENTER, textColor=MUTED)),
        PageBreak(),
    ]

    i, first_h1 = 0, True
    pending_list, list_ordered = [], False

    def flush_list():
        nonlocal pending_list
        if pending_list:
            flow.append(ListFlowable(
                pending_list, bulletType='1' if list_ordered else 'bullet',
                bulletColor=ACCENT, leftIndent=14, bulletFontSize=8))
            flow.append(Spacer(1, 3))
            pending_list = []

    while i < len(md):
        line = md[i].rstrip()
        # Tables
        if line.startswith('|'):
            flush_list()
            tbl = []
            while i < len(md) and md[i].lstrip().startswith('|'):
                tbl.append(md[i]); i += 1
            data = []
            for r, raw in enumerate(tbl):
                if re.match(r'^\s*\|[\s:|-]+\|\s*$', raw):  # separator row
                    continue
                cells = [c.strip() for c in raw.strip().strip('|').split('|')]
                stylekey = 'cellh' if r == 0 else 'cell'
                data.append([Paragraph(inline(c), st[stylekey]) for c in cells])
            if data:
                t = Table(data, repeatRows=1, hAlign='LEFT')
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), INK),
                    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfd6e6')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f7fc')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                flow += [t, Spacer(1, 6)]
            continue

        if not line.strip():
            flush_list(); i += 1; continue
        if line.startswith('# '):
            flush_list()
            if first_h1:
                first_h1 = False; i += 1; continue  # title page already covers it
            flow.append(Paragraph(inline(line[2:]), st['h1']))
        elif line.startswith('## '):
            flush_list()
            flow.append(Paragraph(inline(line[3:]), st['h2']))
            flow.append(HRFlowable(width='100%', color=colors.HexColor('#e3e8f1'), spaceAfter=4))
        elif line.startswith('### '):
            flush_list(); flow.append(Paragraph(inline(line[4:]), st['h3']))
        elif line.startswith('---'):
            flush_list()
        elif line.startswith('>'):
            flush_list()
            flow.append(Paragraph(inline(line.lstrip('> ').rstrip()), st['quote']))
        elif re.match(r'^\d+\.\s+', line):
            if pending_list and not list_ordered:
                flush_list()
            list_ordered = True
            pending_list.append(ListItem(Paragraph(inline(re.sub(r'^\d+\.\s+', '', line)), st['li']),
                                         value=int(re.match(r'^(\d+)\.', line).group(1))))
        elif re.match(r'^[-*]\s+', line):
            if pending_list and list_ordered:
                flush_list()
            list_ordered = False
            pending_list.append(ListItem(Paragraph(inline(re.sub(r'^[-*]\s+', '', line)), st['li'])))
        else:
            flush_list()
            flow.append(Paragraph(inline(line), st['body']))
        i += 1
    flush_list()

    out = ROOT / 'OPERATING_MANUAL.pdf'
    doc = SimpleDocTemplate(str(out), pagesize=A4, title='PharmaDesk Operating Manual',
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm)

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10 * mm, f'{shop} - PharmaDesk Operating Manual')
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f'Page {d.page}')
        canvas.restoreState()

    doc.build(flow, onLaterPages=footer)
    print(f'Wrote {out} ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--shop', default='Sri Sakthi Medicals')
    build(ap.parse_args().shop)
