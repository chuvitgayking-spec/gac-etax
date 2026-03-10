"""
PDF Generation Module for e-Tax Invoice System
Generates professional tax invoices in PDF format
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from decimal import Decimal
from datetime import datetime
import os

# Company information
COMPANY_NAME = "GULF AGENCY COMPANY (THAILAND) LTD."
COMPANY_ADDRESS = "26/30-31 9TH FL., ORAKARN BLDG., SOI CHIDLOM\nPLOENCHIT RD., LUMPINEE, PATHUMWAN, BANGKOK"
COMPANY_TAX_ID = "0105535169497"
COMPANY_PHONE = "02-650-7400"
COMPANY_EMAIL = "thailand@gac.com"

def create_receipt_pdf(invoice_data, output_path):
    """
    Create a tax receipt PDF
    
    Args:
        invoice_data: Dictionary with invoice information
        output_path: Path to save PDF
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT
    )
    
    right_style = ParagraphStyle(
        'Right',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT
    )
    
    # Build content
    story = []
    
    # Header - Company Name
    story.append(Paragraph(COMPANY_NAME, title_style))
    story.append(Paragraph(f"TAX ID: {COMPANY_TAX_ID}", header_style))
    story.append(Paragraph(COMPANY_ADDRESS.replace('\n', '<br/>'), header_style))
    story.append(Paragraph(f"Tel: {COMPANY_PHONE} | Email: {COMPANY_EMAIL}", header_style))
    story.append(Spacer(1, 10))
    
    # Invoice Info Table
    info_data = [
        ['Invoice No:', invoice_data.get('invoice_no', ''), 'Running No:', invoice_data.get('running_no', '')],
        ['Date:', invoice_data.get('invoice_date', ''), 'Customer:', invoice_data.get('customer_name', '')],
    ]
    
    info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))
    
    # Items Table
    items = invoice_data.get('items', [])
    
    # Separate items by VAT type
    non_vat_items = [i for i in items if i['vat_rate'] == 0]
    vat_items = [i for i in items if i['vat_rate'] > 0]
    
    # Header row
    table_data = [['No.', 'Description', 'Amount (USD)', 'VAT%', 'VAT Amount', 'Amount (THB)']]
    
    # Non-VAT items
    for item in non_vat_items:
        table_data.append([
            str(item['item_no']),
            item['description'][:30],
            f"${item['amount']:,.2f}",
            '0%',
            '-',
            f"฿{item['amount_thb']:,.2f}"
        ])
    
    # VAT items
    for item in vat_items:
        table_data.append([
            str(item['item_no']),
            item['description'][:30],
            f"${item['amount']:,.2f}",
            '7%',
            f"${item['vat_amount']:,.2f}",
            f"฿{item['amount_thb'] + item['vat_amount_thb']:,.2f}"
        ])
    
    # Create table
    col_widths = [1*cm, 8*cm, 3*cm, 2*cm, 3*cm, 4*cm]
    items_table = Table(table_data, colWidths=col_widths)
    
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 15))
    
    # Totals
    subtotal = Decimal(str(invoice_data.get('subtotal', 0)))
    vat = Decimal(str(invoice_data.get('vat_amount', 0)))
    total = Decimal(str(invoice_data.get('total_amount', 0)))
    total_thb = Decimal(str(invoice_data.get('total_thb', 0)))
    exchange_rate = Decimal(str(invoice_data.get('exchange_rate', 30.909)))
    
    totals_data = [
        ['Subtotal:', f"${subtotal:,.2f}"],
        ['VAT 7%:', f"${vat:,.2f}"],
        ['TOTAL USD:', f"${total:,.2f}"],
        [f'Exchange Rate: 1 USD = {exchange_rate} THB', f"Total: ฿{total_thb:,.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[15*cm, 5*cm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(totals_table)
    story.append(Spacer(1, 20))
    
    # Signature lines
    signature_data = [
        ['_________________________', '_________________________'],
        ['Authorized Signature', 'Received By']
    ]
    
    sig_table = Table(signature_data, colWidths=[8*cm, 8*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Oblique'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    story.append(sig_table)
    
    # Build PDF
    doc.build(story)
    
    return output_path

def create_xml_etax(invoice_data, output_path):
    """
    Create e-Tax XML file for Revenue Department
    
    Args:
        invoice_data: Dictionary with invoice information
        output_path: Path to save XML
    """
    from lxml import etree
    
    # Build XML structure according to e-Tax standard
    root = etree.Element('Invoice')
    
    # Header
    header = etree.SubElement(root, 'Header')
    etree.SubElement(header, 'InvoiceNumber').text = invoice_data.get('invoice_no', '')
    etree.SubElement(header, 'InvoiceDate').text = invoice_data.get('invoice_date', '')
    etree.SubElement(header, 'ReferenceNumber').text = invoice_data.get('running_no', '')
    
    # Seller
    seller = etree.SubElement(root, 'Seller')
    etree.SubElement(seller, 'TaxID').text = COMPANY_TAX_ID
    etree.SubElement(seller, 'Name').text = COMPANY_NAME
    etree.SubElement(seller, 'Address').text = COMPANY_ADDRESS.replace('\n', ', ')
    etree.SubElement(seller, 'PhoneNumber').text = COMPANY_PHONE
    
    # Buyer
    buyer = etree.SubElement(root, 'Buyer')
    buyer_name = invoice_data.get('customer_name', 'Unknown')
    etree.SubElement(buyer, 'Name').text = buyer_name
    etree.SubElement(buyer, 'TaxID').text = invoice_data.get('customer_tax_id', '')
    
    # Items
    items = etree.SubElement(root, 'Items')
    
    for item in invoice_data.get('items', []):
        item_elem = etree.SubElement(items, 'Item')
        etree.SubElement(item_elem, 'Number').text = str(item['item_no'])
        etree.SubElement(item_elem, 'Description').text = item['description']
        etree.SubElement(item_elem, 'Quantity').text = '1'
        etree.SubElement(item_elem, 'UnitCode').text = 'UN'
        etree.SubElement(item_elem, 'UnitPrice').text = str(item['amount'])
        etree.SubElement(item_elem, 'Total').text = str(item['amount'])
        etree.SubElement(item_elem, 'VatRate').text = str(item['vat_rate'])
        etree.SubElement(item_elem, 'VatAmount').text = str(item['vat_amount'])
    
    # Summary
    summary = etree.SubElement(root, 'Summary')
    etree.SubElement(summary, 'SubTotal').text = str(invoice_data.get('subtotal', 0))
    etree.SubElement(summary, 'VatTotal').text = str(invoice_data.get('vat_amount', 0))
    etree.SubElement(summary, 'TotalAmount').text = str(invoice_data.get('total_amount', 0))
    etree.SubElement(summary, 'CurrencyCode').text = 'USD'
    etree.SubElement(summary, 'ExchangeRate').text = str(invoice_data.get('exchange_rate', 1))
    etree.SubElement(summary, 'TotalAmountTHB').text = str(invoice_data.get('total_thb', 0))
    
    # Write XML
    tree = etree.ElementTree(root)
    tree.write(output_path, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    
    return output_path
