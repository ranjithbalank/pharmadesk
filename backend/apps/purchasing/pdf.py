"""Purchase-order PDF (item 5): shop logo + address + GST, bill-to / ship-to,
its own document number, and per-line HSN. Generated locally with ReportLab.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from apps.core.models import ShopSetting


def purchase_order_pdf(po):
    shop = ShopSetting.load()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm, title=po.number,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle('t', parent=styles['Title'], fontSize=15, spaceAfter=2)
    small = ParagraphStyle('s', parent=styles['Normal'], fontSize=8, leading=11)
    label = ParagraphStyle('l', parent=small, textColor=colors.HexColor('#5b6781'))

    # --- Header: logo + shop identity --------------------------------------
    licence = (f' &nbsp;&nbsp; DL No: {shop.drug_licence_no}'
               if shop.has_drug_license and shop.drug_licence_no else '')
    identity = Paragraph(
        f'{shop.address or ""}<br/>GSTIN: {shop.gstin or "-"}{licence}'
        + (f'<br/>Ph: {shop.phone}' if shop.phone else ''), small,
    )
    header_cells = [[Paragraph(shop.shop_name, title), '']]
    if shop.logo and hasattr(shop.logo, 'path'):
        try:
            logo = Image(shop.logo.path, width=28 * mm, height=28 * mm, kind='proportional')
            header_cells = [[Paragraph(shop.shop_name, title), logo]]
        except Exception:
            pass
    head = Table(header_cells, colWidths=[doc.width - 30 * mm, 30 * mm])
    head.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
    elems = [head, identity, Spacer(1, 4 * mm),
             Paragraph('<b>PURCHASE ORDER</b>', ParagraphStyle(
                 'po', parent=styles['Heading2'], fontSize=12))]

    # --- Meta: number / date / supplier / bill-to / ship-to ----------------
    sup = po.supplier
    meta = [[
        Paragraph(f'<b>PO No:</b> {po.number}<br/><b>Date:</b> '
                  f'{po.created_at:%d-%m-%Y}<br/><b>Status:</b> {po.get_status_display()}', small),
        Paragraph(f'<b>Supplier:</b> {sup.name}'
                  + (f' ({sup.code})' if sup.code else '')
                  + f'<br/>GSTIN: {sup.gstin or "-"}'
                  + (f'<br/>DL No: {sup.drug_license_no}' if sup.has_drug_license and sup.drug_license_no else '')
                  + (f'<br/>{sup.phone}' if sup.phone else ''), small),
    ]]
    meta_t = Table(meta, colWidths=[doc.width / 2] * 2)
    meta_t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfd6e6')),
                               ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfd6e6')),
                               ('LEFTPADDING', (0, 0), (-1, -1), 6),
                               ('TOPPADDING', (0, 0), (-1, -1), 5),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    elems += [Spacer(1, 2 * mm), meta_t]

    bill_to = po.bill_to or f'{shop.shop_name}\n{shop.address}'
    ship_to = po.ship_to or bill_to
    addr = [[Paragraph('<b>Bill to</b>', label), Paragraph('<b>Ship to</b>', label)],
            [Paragraph(bill_to.replace('\n', '<br/>'), small),
             Paragraph(ship_to.replace('\n', '<br/>'), small)]]
    addr_t = Table(addr, colWidths=[doc.width / 2] * 2)
    addr_t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfd6e6')),
                               ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfd6e6')),
                               ('LEFTPADDING', (0, 0), (-1, -1), 6),
                               ('TOPPADDING', (0, 0), (-1, -1), 5),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    elems += [Spacer(1, 2 * mm), addr_t, Spacer(1, 4 * mm)]

    # --- Line items with HSN ----------------------------------------------
    rows = [['#', 'Medicine', 'HSN', 'GST%', 'Qty', 'Unit cost', 'Amount']]
    for i, line in enumerate(po.lines.all(), 1):
        rows.append([
            str(i), line.medicine.name, line.medicine.hsn_code or '-',
            f'{line.medicine.gst_rate:.0f}', str(line.quantity),
            f'{line.unit_cost:.2f}', f'{line.quantity * line.unit_cost:.2f}',
        ])
    rows.append(['', '', '', '', '', 'Total', f'{po.total_value:.2f}'])
    col_w = [8, 150, 32, 26, 24, 40, 44]
    items = Table(rows, colWidths=[w * (doc.width / sum(col_w)) for w in col_w], repeatRows=1)
    items.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e2640')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -2), 0.4, colors.HexColor('#cfd6e6')),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f4f7fc')]),
        ('LINEABOVE', (0, -1), (-1, -1), 0.6, colors.black),
        ('FONTNAME', (5, -1), (-1, -1), 'Helvetica-Bold'),
        ('SPAN', (0, -1), (4, -1)),
    ]))
    elems += [items, Spacer(1, 8 * mm)]
    if po.notes:
        elems.append(Paragraph(f'<b>Notes:</b> {po.notes}', small))
    elems += [Spacer(1, 14 * mm),
              Paragraph('Authorised signature: ______________________', small)]

    doc.build(elems)
    return buf.getvalue()
