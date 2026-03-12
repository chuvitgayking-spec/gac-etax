from playwright.sync_api import sync_playwright
from io import BytesIO
import tempfile
import os

def generate_receipt_pdf(invoice_data):
    """Generate PDF using Playwright - exact HTML match with Thai support"""
    
    # Get values
    subtotal = float(invoice_data.get('total_amount', 0) or 0)
    exchange_rate = float(invoice_data.get('exchange_rate', 1) or 1)
    total_thb = float(invoice_data.get('total_thb', 0) or 0)
    if total_thb == 0 and subtotal > 0:
        total_thb = subtotal * exchange_rate
    vat = total_thb - (total_thb / 1.07)
    
    invoice_no = invoice_data.get('invoice_no', '-')
    customer = invoice_data.get('customer_name', 'Customer')
    address = invoice_data.get('customer_address', '')[:80]
    date = invoice_data.get('invoice_date', '')
    running = invoice_data.get('running_no', 'Draft')
    
    # Build HTML (same as preview)
    html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; font-size: 11px; color: #000; }
.header { display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 2px solid #000; }
.header-left { width: 50%; }
.header-right { width: 50%; text-align: right; }
.company-name { font-size: 18px; font-weight: bold; color: #0066b2; }
.title { text-align: center; font-size: 18px; font-weight: bold; padding: 10px; border: 2px solid #000; margin: 15px 0; }
.cust-info { display: flex; border: 1px solid #000; margin-bottom: 15px; }
.cust-left { width: 50%; padding: 10px; border-right: 1px solid #000; }
.cust-right { width: 50%; padding: 10px; }
.items-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
.items-table th { background: #eee; padding: 8px; border: 1px solid #000; text-align: center; }
.items-table td { padding: 6px; border: 1px solid #000; }
.totals { width: 50%; margin-left: auto; }
.totals table { width: 100%; }
.totals td { padding: 8px; border: 1px solid #000; }
.footer { display: flex; margin-top: 30px; }
.footer-left { width: 50%; padding: 10px; border: 1px dashed #888; }
.footer-right { width: 50%; padding: 10px; text-align: center; }
.signature { border-top: 1px solid #000; padding-top: 5px; margin-top: 40px; }
.disclaimer { margin-top: 30px; padding-top: 15px; border-top: 1px solid #ccc; font-size: 8px; text-align: center; }
</style>
</head>
<body>
<div class="header">
<div class="header-left">
<div><b>เลขประจำตัวผู้เสียภาษีอากร / Tax ID No. 0105535169497</div>
<div>ทะเบียนการค้า / Registration No. 0105535169497</div>
</div>
<div class="header-right">
<div class="company-name">GULF AGENCY COMPANY (THAILAND) LTD.</div>
<div>บริษัท กัลฟ์ เอเจนซี่ คัมปะนี (ประเทศไทย) จำกัด</div>
<div>26/30-31 ชั้น 9 อาคารอรกาน์ ซอยชิดลม ถนนพระราม 4 แขวงลุมพินี เขตปางคอยแหลม กรุงเทพมหานคร 10330</div>
<div>Tel: 02-650-7400 | Email: thailand@gac.com</div>
</div>
</div>

<div class="title">RECEIPT COPY / TAX INVOICE COPY</div>

<div class="cust-info">
<div class="cust-left">
<div><b>ชื่อลูกค้า / Customer Name:</b></div>
<div>''' + customer + '''</div>
<div>''' + address[:60] + '''</div>
</div>
<div class="cust-right">
<div><b>No. / เลขที่:</b> ''' + running + '''</div>
<div><b>Date / วันที่:</b> ''' + date + '''</div>
<div><b>Invoice No:</b> ''' + invoice_no + '''</div>
</div>
</div>

<table class="items-table">
<tr><th>รายการ / Description</th><th style="text-align:right;">จำนวนเงิน / Amount</th><th style="text-align:right;">VAT 7%</th><th style="text-align:right;">Total (THB)</th></tr>'''
    
    # Add items
    try:
        items = invoice_data.get('items', [])
        if not items and invoice_data.get('items_json'):
            import json
            items = json.loads(invoice_data.get('items_json', '[]'))
        for item in items[:15]:
            desc = item.get('description', '-')[:45]
            amt = float(item.get('amount', 0))
            item_vat = amt * 0.07
            html += f'''<tr><td>{desc}</td><td style="text-align:right;">{amt:,.2f}</td><td style="text-align:right;">{item_vat:,.2f}</td><td style="text-align:right;">{amt:,.2f}</td></tr>'''
    except:
        pass
    
    html += f'''</table>

<div class="totals">
<table>
<tr><td style="text-align:right;"><b>รวมเงิน / Subtotal:</b></td><td style="text-align:right;">{total_thb-vat:,.2f}</td></tr>
<tr><td style="text-align:right;"><b>ภาษีมูลค่าเพิ่ม 7% / VAT 7%:</b></td><td style="text-align:right;">{vat:,.2f}</td></tr>
<tr><td style="text-align:right;font-size:14px;"><b>จำนวนเงินรวม / GRAND TOTAL:</b></td><td style="text-align:right;font-size:14px;"><b>{total_thb:,.2f}</b></td></tr>
</table>
</div>

<div class="footer">
<div class="footer-left">
<div><b>วิธีการชำระเงิน / Payment Method:</b></div>
<div>☐ เงินสด / Cash &nbsp; ☑ เครดิต / Credit &nbsp; ☐ เช็ค / Cheque</div>
<div style="margin-top:10px;border-top:1px dotted #888;padding-top:5px;">Bank: Bangkok Bank | A/C: 123-456-7890</div>
</div>
<div class="footer-right">
<div class="signature">ผู้เก็บเงิน / Bill Collector</div>
<div style="height:20px;"></div>
<div class="signature">Accountant</div>
</div>
</div>

<div class="disclaimer">
<div><b>All business is undertaken subject to our Standard Trading Conditions of Carriage, which are incorporated into all contracts of carriage to which we are a party.</b></div>
<div><b>ใบเสร็จรับเงินนี้จะสมบูรณ์ต่อเมื่อมีลายเซ็นของผู้มีอำนาจและพนักงานเก็บเงินของบริษัทฯ กรณีชำระด้วยเช็ค ใบเสร็จรับเงินนี้จะสมบูรณ์ต่อเมื่อบริษัทฯ ได้รับชำระเงินตามเช็คเรียบร้อยแล้ว</b></div>
<div><i>This receipt is not valid unless signed by authorized person and collector. If payment is made by cheque, this receipt will be valid only when the cheque has been honoured.</i></div>
</div>
</body>
</html>'''
    
    # Generate PDF using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        pdf_data = page.pdf(format='A4', print_background=True, margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'})
        browser.close()
    
    buffer = BytesIO(pdf_data)
    buffer.seek(0)
    return buffer
