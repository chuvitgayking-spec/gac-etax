import weasyprint
from io import BytesIO

def generate_receipt_pdf(invoice_data):
    """Generate PDF using HTML template - exact match with preview"""
    # Build HTML inline (same as get_unified_receipt_html in app.py)
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
    
    # Build HTML exactly like preview
    html = '''<div style="width:100%;padding:15mm;background:#fff;font-family:Arial,sans-serif;font-size:11px;color:#000;">'''
    
    # Header
    html += '''<table style="width:100%;margin-bottom:10px;"><tr>'''
    html += '''<td style="width:50%;vertical-align:top;"><div style="font-weight:bold;">Tax ID No. 0105535169497</div><div>Registration No. 0105535169497</div></td>'''
    html += '''<td style="width:50%;text-align:right;vertical-align:top;"><div style="font-size:18px;font-weight:bold;color:#0066b2;">GULF AGENCY COMPANY (THAILAND) LTD.</div><div>26/30-31 9th Floor, Orakarn Building</div><div>Soi Chidlom, Bangkok 10330</div><div>Tel: 02-650-7400</div></td>'''
    html += '''</tr></table>'''
    
    # Title
    html += '<div style="text-align:center;font-size:18px;font-weight:bold;padding:10px;border:2px solid #000;margin:15px 0;">RECEIPT COPY / TAX INVOICE COPY</div>'
    
    # Customer
    html += '''<table style="width:100%;margin-bottom:15px;border:1px solid #000;"><tr>'''
    html += '''<td style="width:50%;padding:10px;border:1px solid #000;"><div style="font-weight:bold;">Customer Name:</div><div>''' + str(customer) + '''</div><div>''' + str(address)[:60] + '''</div></td>'''
    html += '''<td style="width:50%;padding:10px;border:1px solid #000;"><div><b>No:</b> ''' + str(running) + '''</div><div><b>Date:</b> ''' + str(date) + '''</div><div><b>Invoice No:</b> ''' + str(invoice_no) + '''</div></td>'''
    html += '''</tr></table>'''
    
    # Items header
    html += '''<table style="width:100%;margin-bottom:15px;border:1px solid #000;border-collapse:collapse;">'''
    html += '''<tr style="background:#eee;"><th style="padding:8px;border:1px solid #000;text-align:center;">Description</th><th style="padding:8px;border:1px solid #000;text-align:right;">Amount</th><th style="padding:8px;border:1px solid #000;text-align:right;">VAT 7%</th><th style="padding:8px;border:1px solid #000;text-align:right;">Total</th></tr>'''
    
    # Items
    try:
        items = invoice_data.get('items', [])
        if not items and invoice_data.get('items_json'):
            import json
            items = json.loads(invoice_data.get('items_json', '[]'))
        for item in items[:15]:
            desc = item.get('description', '-')[:45]
            amt = float(item.get('amount', 0))
            item_vat = amt * 0.07
            html += f'''<tr><td style="padding:6px;border:1px solid #000;">{desc}</td>
            <td style="padding:6px;border:1px solid #000;text-align:right;">{amt:,.2f}</td>
            <td style="padding:6px;border:1px solid #000;text-align:right;">{item_vat:,.2f}</td>
            <td style="padding:6px;border:1px solid #000;text-align:right;">{amt:,.2f}</td></tr>'''
    except:
        pass
    
    html += '</table>'
    
    # Totals
    html += f'''<table style="width:50%;margin-left:auto;">
    <tr><td style="padding:8px;text-align:right;">Subtotal:</td><td style="padding:8px;text-align:right;border:1px solid #000;">{total_thb-vat:,.2f}</td></tr>
    <tr><td style="padding:8px;text-align:right;">VAT 7%:</td><td style="padding:8px;text-align:right;border:1px solid #000;">{vat:,.2f}</td></tr>
    <tr><td style="padding:10px;text-align:right;font-size:14px;">GRAND TOTAL:</td><td style="padding:10px;text-align:right;border:2px solid #000;font-size:14px;font-weight:bold;">{total_thb:,.2f}</td></tr>
    </table>'''
    
    # Footer
    html += '''<table style="width:100%;margin-top:30px;"><tr>'''
    html += '''<td style="width:50%;padding:10px;border:1px dashed #888;"><div><b>Payment Method:</b> Cash / Credit / Cheque</div><div>Bank: Bangkok Bank | A/C: 123-456-7890</div></td>'''
    html += '''<td style="width:50%;padding:10px;text-align:center;"><div style="border-top:1px solid #000;padding-top:5px;">Bill Collector</div><div style="height:20px;"></div><div style="border-top:1px solid #000;padding-top:5px;">Accountant</div></td>'''
    html += '''</tr></table>'''
    
    # Disclaimer
    html += '''<div style="margin-top:30px;border-top:1px solid #ccc;padding-top:15px;font-size:8px;text-align:center;">'''
    html += '''All business is undertaken subject to our Standard Trading Conditions.<br>'''
    html += '''This receipt is not valid unless signed by authorized person and collector.'''
    html += '''</div>'''
    
    html += '</div>'
    
    # Full HTML
    full_html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>@page {{ size: A4; margin: 0; }}</style></head><body>{html}</body></html>'''
    
    # Convert to PDF using weasyprint
    pdf = weasyprint.HTML(string=full_html).write_pdf()
    
    buffer = BytesIO(pdf)
    buffer.seek(0)
    return buffer
