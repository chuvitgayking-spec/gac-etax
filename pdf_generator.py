from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO

def generate_receipt_pdf(invoice_data):
    """Generate receipt PDF matching HTML preview exactly"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*cm, bottomMargin=0.5*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    
    elements = []
    
    # ===== HEADER =====
    # Header table - Left: Tax ID, Right: Company Info
    header_data = [
        ['เลขประจำตัวผู้เสียภาษีอากร / Tax ID No. 0105535169497\nทะเบียนการค้า / Registration No. 0105535169497',
         'GULF AGENCY COMPANY (THAILAND) LTD.\nบริษัท กัลฟ์ เอเจนซี่ คัมปะนี (ประเทศไทย) จำกัด\n26/30-31 ชั้น 9 อาคารอรกาน์ ซอยชิดลม ถนนพระราม 4\nแขวงลุมพินี เขตปางคอยแหลม กรุงเทพมหานคร 10330\nTel: 02-650-7400 | Email: thailand@gac.com']
    ]
    header_table = Table(header_data, colWidths=[8.5*cm, 9.5*cm])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*cm))
    
    # ===== TITLE =====
    title_style = ParagraphStyle('Title', fontSize=18, bold=True, alignment=1, textColor=colors.black)
    elements.append(Paragraph("RECEIPT COPY / TAX INVOICE COPY", title_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # ===== CUSTOMER & DOC INFO =====
    invoice_no = invoice_data.get('invoice_no', '-')
    running_no = invoice_data.get('running_no', 'Draft')
    invoice_date = invoice_data.get('invoice_date', '-')
    customer = invoice_data.get('customer_name', 'Customer')
    customer_address = invoice_data.get('customer_address', '')
    
    cust_data = [
        ['ชื่อลูกค้า / Customer Name:\n' + customer + '\n' + customer_address[:80],
         'No. / เลขที่: ' + str(running_no) + '\nDate / วันที่: ' + str(invoice_date) + '\nInvoice No: ' + str(invoice_no)]
    ]
    cust_table = Table(cust_data, colWidths=[10*cm, 8*cm])
    cust_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(cust_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # ===== ITEMS TABLE =====
    items = invoice_data.get('items', [])
    if not items:
        items = [{'description': 'Service Charges', 'amount': 0}]
    
    table_data = [['รายการ / Description', 'จำนวนเงิน / Amount', 'VAT 7%', 'Total (THB)']]
    
    for item in items[:15]:
        desc = item.get('description', '-')[:40]
        amt = float(item.get('amount', 0))
        vat = amt * 0.07
        table_data.append([desc, f"{amt:,.2f}", f"{vat:,.2f}", f"{amt:,.2f}"])
    
    # Calculate totals
    exchange_rate = float(invoice_data.get('exchange_rate', 1) or 1)
    total_usd = float(invoice_data.get('total_amount', 0) or 0)
    total_thb = float(invoice_data.get('total_thb', 0) or 0)
    if total_thb == 0 and total_usd > 0:
        total_thb = total_usd * exchange_rate
    vat_total = total_thb - (total_thb / 1.07)
    subtotal = total_thb - vat_total
    
    items_table = Table(table_data, colWidths=[9*cm, 3*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # ===== TOTALS =====
    totals_data = [
        ['รวมเงิน / Subtotal:', f"{subtotal:,.2f}"],
        ['ภาษีมูลค่าเพิ่ม 7% / VAT 7%:', f"{vat_total:,.2f}"],
        ['จำนวนเงินรวม / GRAND TOTAL:', f"{total_thb:,.2f}"]
    ]
    totals_table = Table(totals_data, colWidths=[14*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # ===== FOOTER =====
    footer_data = [
        ['วิธีการชำระเงิน / Payment Method:\n☐ เงินสด / Cash  ☐ เครดิต / Credit  ☐ เช็ค / Cheque\nBank: Bangkok Bank | A/C: 123-456-7890',
         '________________________\nผู้เก็บเงิน / Bill Collector\n\n________________________\nAccountant']
    ]
    footer_table = Table(footer_data, colWidths=[12*cm, 6*cm])
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(footer_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # ===== DISCLAIMER =====
    disc_style = ParagraphStyle('Disc', fontSize=7, alignment=0, spaceAfter=4, leftIndent=0)
    elements.append(Paragraph("<b>All business is undertaken subject to our Standard Trading Conditions of Carriage, which are incorporated into all contracts of carriage to which we are a party.</b>", disc_style))
    elements.append(Paragraph("<b>ใบเสร็จรับเงินนี้จะสมบูรณ์ต่อเมื่อมีลายเซ็นของผู้มีอำนาจและพนักงานเก็บเงินของบริษัทฯ กรณีชำระด้วยเช็ค ใบเสร็จรับเงินนี้จะสมบูรณ์ต่อเมื่อบริษัทฯ ได้รับชำระเงินตามเช็คเรียบร้อยแล้ว</b>", disc_style))
    elements.append(Paragraph("<i>This receipt is not valid unless signed by authorized person and collector. If payment is made by cheque, this receipt will be valid only when the cheque has been honoured.</i>", disc_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
