from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO

def generate_receipt_pdf(invoice_data):
    """Generate receipt PDF matching the sample format"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*cm, bottomMargin=0.5*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Company Info
    company_style = ParagraphStyle('Company', fontSize=14, bold=True, alignment=1)
    address_style = ParagraphStyle('Address', fontSize=9, alignment=1)
    tax_style = ParagraphStyle('Tax', fontSize=8, alignment=1)
    
    elements.append(Paragraph("GAC (THAILAND) CO., LTD.", company_style))
    elements.append(Paragraph("9/2 Sathorn 39, South Sathorn Road, Yannawa, Sathorn", address_style))
    elements.append(Paragraph("Bangkok 10120, Thailand", address_style))
    elements.append(Paragraph("Tel: +66 2 676 1900 | Fax: +66 2 676 1990", address_style))
    elements.append(Paragraph("Tax ID: 0105548024532", tax_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Title
    title_style = ParagraphStyle('Title', fontSize=16, bold=True, alignment=1)
    elements.append(Paragraph("INVOICE / RECEIPT", title_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Invoice Info
    invoice_no = invoice_data.get('invoice_no', '-')
    running_no = invoice_data.get('running_no', '26-0001')
    invoice_date = invoice_data.get('invoice_date', '-')
    customer = invoice_data.get('customer_name', 'Customer')
    job_no = invoice_data.get('job_number', '-')
    exchange_rate = float(invoice_data.get('exchange_rate', 30.909))
    
    info_data = [
        ['Invoice No:', invoice_no, 'Running No:', running_no],
        ['Date:', invoice_date, 'Job No:', job_no],
        ['Customer:', customer, '', ''],
    ]
    
    info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Items Table
    items = invoice_data.get('items', [])
    if not items:
        items = [{'description': 'Freight Charges', 'amount': float(invoice_data.get('total_amount', 0)) / 1.07, 'vat_rate': 7}]
    
    table_data = [['#', 'Description', 'Amount (THB)', 'VAT%', 'VAT (THB)', 'Total (THB)']]
    
    for i, item in enumerate(items):
        desc = item.get('description', 'Item')[:30]
        amount_usd = float(item.get('amount', 0))
        amount_thb = amount_usd * exchange_rate
        vat_rate = item.get('vat_rate', 7)
        vat_thb = amount_thb * (vat_rate / 100)
        total_thb = amount_thb + vat_thb
        
        table_data.append([
            str(i+1),
            desc,
            f"{amount_thb:,.2f}",
            str(vat_rate),
            f"{vat_thb:,.2f}",
            f"{total_thb:,.2f}"
        ])
    
    # Totals
    total_usd = float(invoice_data.get('total_amount', 0))
    total_thb = total_usd * exchange_rate
    vat_thb = total_thb - (total_usd / 1.07 * exchange_rate)
    subtotal_thb = total_thb - vat_thb
    
    table_data.append(['', '', '', 'Subtotal:', f"{subtotal_thb:,.2f}"])
    table_data.append(['', '', '', 'VAT 7%:', f"{vat_thb:,.2f}"])
    table_data.append(['', '', '', 'TOTAL:', f"{total_thb:,.2f}"])
    
    items_table = Table(table_data, colWidths=[1*cm, 7*cm, 3*cm, 1.5*cm, 2.5*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Exchange Rate
    rate_style = ParagraphStyle('Rate', fontSize=9, alignment=1)
    elements.append(Paragraph(f"Exchange Rate: 1 USD = {exchange_rate:.4f} THB", rate_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Footer
    footer_style = ParagraphStyle('Footer', fontSize=7, alignment=1, textColor=colors.grey)
    elements.append(Paragraph("This invoice is subject to GAC Thailand Standard Terms and Conditions", footer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
