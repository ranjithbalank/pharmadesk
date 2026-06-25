"""Generate QUICK_REFERENCE.pdf - a one-page counter card to tape by the till.

    backend/venv/Scripts/python tools/build_quickref.py [--shop "Shop Name"]
"""
import argparse
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
ACCENT = colors.HexColor('#2f6df0')
INK = colors.HexColor('#1e2640')
MUTED = colors.HexColor('#5b6781')
SOFT = colors.HexColor('#f4f7fc')

H = ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=11, textColor=ACCENT, spaceAfter=3)
B = ParagraphStyle('b', fontName='Helvetica', fontSize=9.5, leading=13, textColor=INK)
BIG = ParagraphStyle('big', fontName='Helvetica-Bold', fontSize=12.5, textColor=ACCENT, spaceAfter=4)
STEP = ParagraphStyle('s', fontName='Helvetica', fontSize=10, leading=15, textColor=INK)


def box(title, body_html, big=False):
    """A single bordered card cell: heading + body."""
    cell = [Paragraph(title, BIG if big else H), Paragraph(body_html, STEP if big else B)]
    t = Table([[cell]], colWidths=[None])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), SOFT),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d7deeb')),
        ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def build(shop):
    doc = SimpleDocTemplate(str(ROOT / 'QUICK_REFERENCE.pdf'), pagesize=A4,
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title='PharmaDesk Quick Reference')
    W = doc.width

    header = Table([[
        Paragraph('PharmaDesk &nbsp;-&nbsp; Counter Quick Reference',
                  ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=16, textColor=colors.white)),
        Paragraph(shop, ParagraphStyle('s', fontName='Helvetica', fontSize=10,
                                       textColor=colors.white, alignment=2)),
    ]], colWidths=[W * 0.62, W * 0.38])
    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), INK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 12), ('RIGHTPADDING', (-1, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    bill = box('MAKE A BILL  (press F2)',
               '<b>1.</b>  Search the medicine (press <b>F3</b>) and click it to add to the bill.<br/>'
               '<b>2.</b>  Set the <b>Qty</b>. Add more medicines the same way. Add a discount if needed.<br/>'
               '<b>3.</b>  Choose the customer - pick from the list, or type <b>phone / ID</b> and Fetch. '
               '(Leave as Walk-in if none.)<br/>'
               '<b>4.</b>  Pick payment: <b>Cash / UPI / Card / Credit</b>.<br/>'
               '<b>5.</b>  Click <b>Save &amp; bill</b>, then <b>Print / PDF</b>.  Click <b>New bill</b> for the next customer.',
               big=True)

    loose = box('Loose tablets',
                'Customer wants a few tablets, not a full strip?<br/>'
                'On that line, switch <b>Pack -&gt; Loose</b> and type the <b>number of tablets</b>. '
                'Price becomes per-tablet; the rest of the strip stays in stock.')
    sched = box('Scheduled drugs (H / H1 / X)',
                'A yellow box appears. Enter <b>Patient name</b> and <b>Doctor name</b> '
                'before saving - this builds the legal H1 register automatically.')
    keys = box('Shortcuts',
               '<b>F2</b> &nbsp; Go to Billing<br/>'
               '<b>F3</b> &nbsp; Jump to medicine search<br/>'
               '<b>Enter</b> &nbsp; (in fetch box) look up customer')
    endday = box('End of day',
                 'Billing -&gt; <b>Day close - cash recon</b>.<br/>'
                 'Match <b>Cash in drawer</b> against the physical cash. See the split by Cash/UPI/Card/Credit.')
    alerts = box('Alerts',
                 'The <b>Bell</b> (top-right) shows <b>low stock</b>, <b>out of stock</b>, '
                 'and <b>near-expiry</b> items. A red number means action is needed.')
    bills = box('Give bills to the accountant',
                'Billing -&gt; <b>Download bills</b> -&gt; <b>This month</b> -&gt; <b>Download Excel</b>. '
                'Two sheets: a bill summary and full item detail.')

    def row(a, b):
        t = Table([[a, b]], colWidths=[W / 2 - 3, W / 2 - 3])
        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('LEFTPADDING', (0, 0), (-1, -1), 0),
                               ('RIGHTPADDING', (0, 0), (0, 0), 6),
                               ('LEFTPADDING', (1, 0), (1, 0), 6),
                               ('RIGHTPADDING', (-1, 0), (-1, 0), 0)]))
        return t

    foot = Paragraph(
        'The system always sells the <b>earliest-expiring batch</b> first.  '
        'Sign in: <b>admin</b> (change the password in Settings after go-live).  '
        'Everything works offline - no internet needed.',
        ParagraphStyle('f', fontName='Helvetica', fontSize=8.5, textColor=MUTED, leading=12))

    doc.build([
        header, Spacer(1, 8), bill, Spacer(1, 7),
        row(loose, sched), Spacer(1, 7),
        row(keys, endday), Spacer(1, 7),
        row(alerts, bills), Spacer(1, 9), foot,
    ])
    out = ROOT / 'QUICK_REFERENCE.pdf'
    print(f'Wrote {out} ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--shop', default='Sri Sakthi Medicals')
    build(ap.parse_args().shop)
