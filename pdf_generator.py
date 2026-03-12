from fpdf import FPDF
from io import BytesIO

def generate_receipt_pdf(invoice_data):
    """Generate PDF"""
    pdf = FPDF(format='A4', unit='mm')
    pdf.add_page()
    
    subtotal = float(invoice_data.get('total_amount', 0) or 0)
    exchange_rate = float(invoice_data.get('exchange_rate', 1) or 1)
    total_thb = float(invoice_data.get('total_thb', 0) or 0)
    if total_thb == 0 and subtotal > 0:
        total_thb = subtotal * exchange_rate
    vat = total_thb - (total_thb / 1.07)
    
    invoice_no = invoice_data.get('invoice_no', '-')
    customer = invoice_data.get('customer_name', 'Customer')
    address = invoice_data.get('customer_address', '')[:60]
    date = invoice_data.get('invoice_date', '')
    running = invoice_data.get('running_no', 'Draft')
    
    # Header
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(90, 5, 'Tax ID No. 0105535169497', ln=0)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(90, 5, 'GULF AGENCY COMPANY (THAILAND) LTD.', ln=1, align='R')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(90, 4, 'Registration No. 0105535169497', ln=0)
    pdf.cell(90, 4, '26/30-31 9th Floor, Orakarn Building', ln=1, align='R')
    pdf.cell(90, 4, '', ln=0)
    pdf.cell(90, 4, 'Soi Chidlom, Bangkok 10330', ln=1, align='R')
    pdf.cell(90, 4, '', ln=0)
    pdf.cell(90, 4, 'Tel: 02-650-7400', ln=1, align='R')
    pdf.ln(5)
    
    # Title
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'RECEIPT COPY / TAX INVOICE COPY', ln=1, align='C')
    pdf.ln(5)
    
    # Customer
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(95, 5, 'Customer Name:', ln=1)
    pdf.set_font('helvetica', '', 9)
    pdf.cell(95, 5, customer[:50], ln=1)
    pdf.cell(95, 5, address[:50], ln=1)
    
    pdf.set_xy(110, pdf.get_y() - 15)
    pdf.cell(45, 5, f'No: {running}', ln=1)
    pdf.cell(45, 5, f'Date: {date}', ln=1)
    pdf.cell(45, 5, f'Invoice No: {invoice_no}', ln=1)
    pdf.ln(5)
    
    # Items Header
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(100, 8, 'Description', 1, 0, 'C', 1)
    pdf.cell(30, 8, 'Amount', 1, 0, 'R', 1)
    pdf.cell(30, 8, 'VAT 7%', 1, 0, 'R', 1)
    pdf.cell(30, 8, 'Total', 1, 1, 'R', 1)
    
    # Items
    pdf.set_font('helvetica', '', 8)
    items = invoice_data.get('items', [])
    if not items:
        items = [{'description': 'Service Charges', 'amount': 0}]
    
    for item in items[:15]:
        desc = item.get('description', '-')[:45]
        amt = float(item.get('amount', 0))
        item_vat = amt * 0.07
        pdf.cell(100, 7, desc[:45], 1)
        pdf.cell(30, 7, f'{amt:,.2f}', 1, 0, 'R')
        pdf.cell(30, 7, f'{item_vat:,.2f}', 1, 0, 'R')
        pdf.cell(30, 7, f'{amt:,.2f}', 1, 1, 'R')
    
    # Totals
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(130, 8, 'Subtotal:', 0, 0, 'R')
    pdf.cell(30, 8, f'{total_thb - vat:,.2f}', 1, 1, 'R')
    pdf.cell(130, 8, 'VAT 7%:', 0, 0, 'R')
    pdf.cell(30, 8, f'{vat:,.2f}', 1, 1, 'R')
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(130, 10, 'GRAND TOTAL:', 0, 0, 'R')
    pdf.cell(30, 10, f'{total_thb:,.2f}', 1, 1, 'R')
    pdf.ln(5)
    
    # Footer
    pdf.set_font('helvetica', '', 9)
    pdf.cell(95, 8, 'Payment: Cash / Credit / Cheque', 1, 0)
    pdf.cell(95, 8, '', 0, 1)
    pdf.cell(95, 4, 'Bank: Bangkok Bank | A/C: 123-456-7890', 0, 0)
    pdf.cell(95, 8, '________________________', 0, 1, 'R')
    pdf.cell(95, 4, '', 0, 0)
    pdf.cell(95, 4, 'Bill Collector', 0, 1, 'R')
    pdf.cell(95, 8, '', 0, 0)
    pdf.cell(95, 8, '________________________', 0, 1, 'R')
    pdf.cell(95, 4, '', 0, 0)
    pdf.cell(95, 4, 'Accountant', 0, 1, 'R')
    pdf.ln(10)
    
    # Disclaimer
    pdf.set_font('helvetica', 'I', 7)
    pdf.cell(0, 4, 'All business is undertaken subject to our Standard Trading Conditions.', ln=1, align='C')
    pdf.cell(0, 4, 'This receipt is not valid unless signed by authorized person and collector.', ln=1, align='C')
    
    buffer = BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
    return buffer
