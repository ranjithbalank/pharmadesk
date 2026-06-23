"""Server-side invoice PDF (FR-16/17) using ReportLab — generated locally,
no internet needed. Layout is a compact A5-ish tax invoice.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from apps.core.models import ShopSetting


def invoice_pdf(invoice):
    shop = ShopSetting.load()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A5, leftMargin=10 * mm, rightMargin=10 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm, title=invoice.number,
    )
    styles = getSampleStyleSheet()
    h = ParagraphStyle('h', parent=styles['Title'], fontSize=14, spaceAfter=2)
    small = ParagraphStyle('s', parent=styles['Normal'], fontSize=7.5, leading=10)
    right = ParagraphStyle('r', parent=small, alignment=2)

    elems = [
        Paragraph(shop.shop_name, h),
        Paragraph(
            f'{shop.address or ""}<br/>'
            f'GSTIN: {shop.gstin or "-"} &nbsp;&nbsp; DL No: {shop.drug_licence_no or "-"}'
            f'{(" &nbsp;&nbsp; Ph: " + shop.phone) if shop.phone else ""}',
            small,
        ),
        Spacer(1, 4 * mm),
    ]

    cust = invoice.customer
    meta = [
        [Paragraph(f'<b>Tax Invoice:</b> {invoice.number}', small),
         Paragraph(f'<b>Date:</b> {invoice.created_at:%d-%m-%Y %H:%M}', right)],
        [Paragraph(f'<b>Customer:</b> {cust.name if cust else "Walk-in"}', small),
         Paragraph(f'<b>Payment:</b> {invoice.get_payment_mode_display()}', right)],
    ]
    meta_t = Table(meta, colWidths=[doc.width / 2] * 2)
    meta_t.setStyle(TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    elems += [meta_t, Spacer(1, 3 * mm)]

    head = ['#', 'Item', 'HSN', 'Batch', 'Exp', 'Qty', 'Rate', 'GST%', 'Amount']
    rows = [head]
    for i, line in enumerate(invoice.lines.all(), 1):
        rows.append([
            str(i), line.medicine_name, line.hsn_code, line.batch_number,
            line.expiry_date.strftime('%m/%y') if line.expiry_date else '-',
            str(line.quantity), f'{line.rate:.2f}', f'{line.gst_rate:.0f}',
            f'{line.line_total:.2f}',
        ])
    col_w = [7, 95, 28, 40, 22, 20, 35, 24, 38]
    items_t = Table(rows, colWidths=[w * (doc.width / sum(col_w)) for w in col_w], repeatRows=1)
    items_t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e2640')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfd6e6')),
        ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f7fc')]),
    ]))
    elems += [items_t, Spacer(1, 3 * mm)]

    totals = [
        ['Subtotal (taxable)', f'{invoice.subtotal:.2f}'],
        ['CGST', f'{invoice.cgst:.2f}'],
        ['SGST', f'{invoice.sgst:.2f}'],
        ['Discount', f'-{invoice.discount:.2f}'],
        ['Total', f'INR {invoice.total:.2f}'],
    ]
    tot_t = Table(totals, colWidths=[doc.width * 0.6, doc.width * 0.4])
    tot_t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 0.6, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, -1), (-1, -1), 4),
    ]))
    elems += [tot_t, Spacer(1, 6 * mm),
              Paragraph('Goods once sold are subject to applicable rules. '
                        'Computer-generated invoice.', small)]

    doc.build(elems)
    return buf.getvalue()
