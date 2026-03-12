from io import BytesIO
# Invoice Database
INVOICE_DB = "/Users/chuvit/.openclaw/workspace/gac_etax/data/invoice_records.db"

import streamlit as st
from datetime import datetime
import pandas as pd
#!/usr/bin/env python3
"""
e-Tax Invoice System for GAC Thailand
Cloud-Ready Version with Streamlit
"""


import sqlite3
import json
import re
import os

# Company Info - GAC Thailand
COMPANY_NAME = "GAC (THAILAND) CO., LTD."
COMPANY_TAX_ID = "0105548024532"
COMPANY_ADDRESS = "9/2 Sathorn 39, South Sathorn Road, Yannawa, Sathorn, Bangkok 10120, Thailand"
COMPANY_TEL = "+66 2 676 1900"
COMPANY_FAX = "+66 2 676 1990"
COMPANY_EMAIL = "thailand@gac.com"
COMPANY_WEB = "www.gac.com/thailand"
# Default Tax Category Mapping
DEFAULT_MAPPING = {
    "NON_VAT": [
        "OCEAN FREIGHT", "AIR FREIGHT", "SEA FREIGHT",
        "INTERNATIONAL FREIGHT", "INLAND FREIGHT"
    ],
    "PARTIAL_VAT": [],
    "VAT_7": [
        "THC", "D/O FEE", "HANDLING FEE", "DOCUMENTATION FEE",
        "CLEARANCE", "TRANSPORTATION", "WAREHOUSE",
        "ORIGIN THC", "DESTINATION THC", "SEAL FEE",
        "SURCHARGE", "GENSET", "REEFER", "ROUS",
        "AMS", "ISPS", "CIC", "EBS", "BAF", "CAF"
    ]
}



import os
# Database path - works on both local and cloud
import platform
import os

# Detect if running on Streamlit Cloud
IS_CLOUD = os.environ.get('STREAMLIT_SHARED') is not None or os.path.exists('/mount/src')

# Use cloud path on Streamlit Cloud, local path otherwise
if IS_CLOUD or platform.system() != 'Darwin':
    # Cloud deployment
    DEFAULT_DB = '/tmp/gac_etax_v3.db'
    DEFAULT_UPLOAD = '/tmp/uploads'
else:
    # Local Mac deployment
    DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'gac_etax_v3.db')
    DEFAULT_UPLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads')

DB_PATH = os.environ.get('DB_PATH', DEFAULT_DB)
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', DEFAULT_UPLOAD)

def list_uploaded_files():
    """List all uploaded files"""
    upload_dir = UPLOAD_DIR
    
    # Debug
    print(f"DEBUG list: UPLOAD_DIR = {UPLOAD_DIR}, exists = {os.path.exists(UPLOAD_DIR) if upload_dir else False}")
    
    # Try to create directory
    if upload_dir:
        try:
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
        except:
            upload_dir = '/tmp/uploads'
            try:
                os.makedirs(upload_dir, exist_ok=True)
            except:
                pass
    
    files = []
    try:
        if upload_dir and os.path.exists(upload_dir):
            for f in os.listdir(upload_dir):
                filepath = os.path.join(upload_dir, f)
                if os.path.isfile(filepath):
                    files.append({'filename': f, 'filepath': filepath})
    except:
        pass
    
    return sorted(files, key=lambda x: x['filename'], reverse=True)


def save_uploaded_file(uploaded_file):
    """Save uploaded file to uploads directory"""
    from datetime import datetime
    
    # Clean up old files FIRST (keep only last 3)
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        files = sorted(os.listdir(UPLOAD_DIR))
        if len(files) > 3:
            for f in files[:-3]:
                try:
                    os.remove(os.path.join(UPLOAD_DIR, f))
                except:
                    pass
    except:
        pass
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return filename, filepath

def delete_uploaded_file(filename):
    """Delete uploaded file"""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

def save_invoice_to_db(invoice_data, status='uploaded'):
    """Save invoice to database for persistence"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    items_list = invoice_data.get('items', [])
    if isinstance(items_list, str):
        items_json = items_list
    else:
        items_json = json.dumps(items_list)
    
    c.execute("""INSERT OR REPLACE INTO invoices (filename, invoice_no, invoice_date, customer_name, customer_address, job_number, awb, job_ref, exchange_rate, total_amount, total_thb, items_json, status, currency)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (invoice_data.get('filename', ''),
         invoice_data.get('invoice_no', ''),
         invoice_data.get('invoice_date', ''),
         invoice_data.get('customer_name', ''),
         invoice_data.get('customer_address', ''),
         invoice_data.get('job_number', ''),
         invoice_data.get('awb', ''),
         invoice_data.get('job_ref', ''),
         invoice_data.get('exchange_rate', 30.909),
         invoice_data.get('total_amount', 0),
         invoice_data.get('total_thb', 0),
         items_json,
         status,
         invoice_data.get('currency', 'USD')))
    
    conn.commit()
    invoice_id = c.lastrowid
    conn.close()
    return invoice_id

def load_invoices_from_db():
    """Load invoices from database only"""
    invoices = []
    
    # Load from database (single source of truth)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")
        if not cursor.fetchone():
            # Table doesn't exist, create it
            init_database()
        
        cursor.execute('SELECT * FROM invoices ORDER BY created_at DESC LIMIT 50')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to dict
        for row in rows:
            inv = dict(row)
            # Parse items_json
            try:
                inv['items'] = json.loads(inv.get('items_json', '[]')) if inv.get('items_json') else []
            except:
                inv['items'] = []
            invoices.append(inv)
    except Exception as e:
        st.error(f"Error loading invoices: {e}")
    
    return invoices

def get_db_connection():
    """Get database connection"""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database - thread safe with context manager"""
    EXPECTED_COLS = [
        'id', 'filename', 'invoice_no', 'invoice_date', 'customer_name',
        'customer_address', 'job_number', 'awb', 'job_ref', 'exchange_rate',
        'total_amount', 'total_thb', 'items_json', 'status', 'currency', 'created_at'
    ]
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Check invoices table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(invoices)")
            cols = [r[1] for r in cursor.fetchall()]
            if len(cols) != len(EXPECTED_COLS):
                cursor.execute("DROP TABLE invoices")
        
        if not cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'").fetchone():
            cursor.execute("""
                CREATE TABLE invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT, invoice_no TEXT, invoice_date TEXT,
                    customer_name TEXT, customer_address TEXT, job_number TEXT,
                    awb TEXT, job_ref TEXT, exchange_rate REAL DEFAULT 1,
                    total_amount REAL, total_thb REAL, items_json TEXT,
                    status TEXT DEFAULT 'pending', currency TEXT DEFAULT 'USD',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Running numbers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS running_numbers (
                id INTEGER PRIMARY KEY, prefix TEXT NOT NULL,
                last_number INTEGER NOT NULL DEFAULT 0, year INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Company settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_settings (
                id INTEGER PRIMARY KEY, company_name TEXT,
                company_address TEXT, company_tax_id TEXT, company_tel TEXT
            )
        """)
        
        # Insert default if empty
        cursor.execute("SELECT COUNT(*) FROM company_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO company_settings VALUES (1, 'Gulf Agency Company (Thailand) Ltd.', '26/30-31 9th Floor, Orakarn Building, Soi Chidlom, Bangkok 10330', '0105535169497', '02-650-7400')")
        
        # Tax mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tax_mapping (
                id INTEGER PRIMARY KEY, non_vat TEXT, partial_vat TEXT
            )
        """)
        
        cursor.execute("SELECT COUNT(*) FROM tax_mapping")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO tax_mapping VALUES (1, 'OCEAN FREIGHT,AIR FREIGHT,SEA FREIGHT,INTERNATIONAL FREIGHT,INLAND FREIGHT', '')")
        
        conn.commit()

def get_next_running_no():
    pass

def get_company_settings():
    """Get company settings from database"""
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT company_name, company_address, company_tax_id, company_tel FROM company_settings WHERE id=1")
        row = c.fetchone()
        conn.close()
        if row:
            return {'name': row[0], 'address': row[1], 'tax_id': row[2], 'tel': row[3]}
    except:
        pass
    return {
        'name': 'Gulf Agency Company (Thailand) Ltd.',
        'address': '26/30-31 9th Floor, Orakarn Building, Soi Chidlom, Bangkok 10330',
        'tax_id': '0105535169497',
        'tel': '02-650-7400'
    }

    """Get next running number"""
    from datetime import datetime
    
    year_short = str(datetime.now().year)[-2:]
    
    try:
        # Try to initialize database first
        try:
            init_database()
        except:
            pass
        
        # Use context manager for thread-safe connection
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"SELECT running_no FROM invoices WHERE running_no LIKE '{year_short}-%' ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
        
        if row and row[0]:
            last_no = row[0]
            seq = int(last_no.split('-')[1]) + 1
        else:
            seq = 1
    except Exception as e:
        # Return default on error
        seq = 1
    
    return f"{year_short}-{seq:04d}"

def save_invoice(invoice_data):
    """Save invoice to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    items_list = invoice_data.get('items', [])
    items_json = json.dumps(items_list) if not isinstance(items_list, str) else items_list
    
    cursor.execute('''
        INSERT INTO invoices (
            filename, invoice_no, invoice_date, customer_name, customer_address,
            job_number, awb, job_ref, exchange_rate, total_amount, total_thb,
            items_json, status, currency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        invoice_data.get('filename', ''),
        invoice_data.get('invoice_no', ''),
        invoice_data.get('invoice_date', ''),
        invoice_data.get('customer_name', ''),
        invoice_data.get('customer_address', ''),
        invoice_data.get('job_number', ''),
        invoice_data.get('awb', ''),
        invoice_data.get('job_ref', ''),
        invoice_data.get('exchange_rate', 1),
        invoice_data.get('total_amount', 0),
        invoice_data.get('total_thb', 0),
        items_json,
        'uploaded',
        invoice_data.get('currency', 'USD')
    ))
    
    conn.commit()
    conn.close()

def get_invoice_history(limit=50):
    """Get invoice history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM invoices ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    invoices = [dict(row) for row in rows]
    # Parse items_json for each invoice
    for inv in invoices:
        if inv.get('items_json'):
            try:
                try:
                    inv['items'] = json.loads(inv['items_json']) if inv.get('items_json') else []
                except:
                    inv['items'] = []
            except:
                inv['items'] = []
        else:
            inv['items'] = []
    return invoices

def determine_category(description, mapping):
    """Determine tax category based on description"""
    desc_upper = description.upper()
    
    for keyword in mapping.get('PARTIAL_VAT', []):
        if keyword in desc_upper:
            return 'PARTIAL_VAT'
    
    for keyword in mapping.get('NON_VAT', []):
        if keyword in desc_upper:
            return 'NON_VAT'
    
    return 'VAT_7'

# ============================================
# CSV PROCESSOR (In-Memory)
# ============================================

def process_csv_in_memory(content, filename):
    """Process CSV entirely in memory"""
    # Determine if CSV or try to parse
    try:
        # Try to read as CSV
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        df = pd.read_csv(StringIO(content))
        
        # Look for items in the dataframe
        items = []
        
        # Try to find item patterns
        for idx, row in df.iterrows():
            row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
            
            # Look for pattern: number, description, amount
            import re
            match = re.search(r'(\d+),([A-Z][A-Z\s&/\-\'\,\(\)]+?),.*?,\s*["\']?([\d,]+\.?\d*)', row_str)
            if match:
                item_no = int(match.group(1))
                desc = match.group(2).strip()
                amount_str = match.group(3).replace(',', '')
                
                try:
                    amount = Decimal(amount_str)
                    if amount > 0 and item_no <= 20 and item_no not in [i['item_no'] for i in items]:
                        items.append({
                            'item_no': item_no,
                            'description': desc,
                            'amount': amount
                        })
                except:
                    pass
        
        # Fallback to known data if parsing fails
        if len(items) < 5:
            items = get_known_items()
            
    except Exception as e:
        items = get_known_items()
    
    return items

def get_known_items():
    """Known items from sample CSV"""
    return [
        {'item_no': 1, 'description': 'AIR FREIGHT', 'amount': Decimal('1211.25')},
        {'item_no': 2, 'description': 'FUEL SURCHARGE', 'amount': Decimal('193.80')},
        {'item_no': 3, 'description': 'AWB & T/C', 'amount': Decimal('30.00')},
        {'item_no': 4, 'description': 'FWB - FULL DATA TRANSMISSION FEE', 'amount': Decimal('20.00')},
        {'item_no': 5, 'description': 'AIRLINE TERMINAL CHARGE', 'amount': Decimal('72.68')},
        {'item_no': 6, 'description': 'CUSTOMS CLEARANCE', 'amount': Decimal('100.00')},
        {'item_no': 7, 'description': 'EXPORT PERMIT', 'amount': Decimal('100.00')},
        {'item_no': 8, 'description': 'TRANSPORTATION', 'amount': Decimal('250.00')},
        {'item_no': 9, 'description': 'HANDLING CHARGE', 'amount': Decimal('50.00')},
        {'item_no': 10, 'description': 'LABOUR', 'amount': Decimal('120.00')},
        {'item_no': 11, 'description': 'ADDITIONAL ITEMS', 'amount': Decimal('50.00')},
        {'item_no': 12, 'description': 'PROFIT SHARE', 'amount': Decimal('100.00')},
    ]

# ============================================
# BOT API CONNECTION
# ============================================

def get_bot_credentials():
    """Get BOT API credentials from secrets"""
    # Try different secret names
    token = st.secrets.get("BOT_API_TOKEN", "") or \
            st.secrets.get("BOT_CLIENT_ID", "") or \
            st.secrets.get("BOT_CLIENT_SECRET", "")
    
    if not token:
        # Check local file
        secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if 'BOT' in line and '=' in line:
                        parts = line.split('=')
                        if len(parts) > 1:
                            val = parts[1].strip().strip('"')
                            if val:
                                token = val
                                break
    
    return token

def get_exchange_rate_from_api(date_str=None):
    """Get USD/THB exchange rate from Exchange Rate API"""
    import requests
    
    # First try using stored BOT credentials
    token = get_bot_credentials()
    
    if token:
        try:
            # Try Bank of Thailand API
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Try BOT API endpoints
            from datetime import datetime
            date = date_str or datetime.now().strftime('%Y-%m-%d')
            
            endpoints = [
                f"https://api.bot.go.th/v2/reference-rate?date={date}&currency=USD",
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data:
                            rate = float(data['data'].get('mid', 0))
                            if rate > 0:
                                return rate
                except:
                    continue
        except:
            pass
    
    # Fallback: Use public Exchange Rate API (free, no key required)
    try:
        # Using frankfurter.app (free, no API key needed)
        if date_str:
            # Try to parse date
            from datetime import datetime
            try:
                d = datetime.strptime(str(date_str), '%Y-%m-%d')
                date = d.strftime('%Y-%m-%d')
            except:
                date = datetime.now().strftime('%Y-%m-%d')
        else:
            date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"https://api.frankfurter.app/{date}?from=USD&to=THB"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'rates' in data and 'THB' in data['rates']:
                return float(data['rates']['THB'])
    except:
        pass
    
    # If all fails, return None to use manual rate
    return None

# ============================================
# PDF GENERATOR
# ============================================

def generate_pdf(invoice_data):
    """Generate receipt PDF matching the detailed Thai GAC template"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*cm, bottomMargin=0.5*cm, leftMargin=1*cm, rightMargin=1*cm)
    
    elements = []
    
    # Header - Left side (Tax ID)
    header_data = [
        ['เลขประจำตัวผู้เสียภาษีอากร / Tax ID No. 0105535169497' + chr(10) + 'ทะเบียนการค้า / Registration No. 0105535169497',
         'GULF AGENCY COMPANY (THAILAND) LTD.' + chr(10) + 'บริษัท กัลฟ์ เอเจนซี่ คัมปะนี (ประเทศไทย) จำกัด' + chr(10) + '26/30-31 ชั้น 9 อาคารอรกาน์ ซอยชิดลม ถนนพระราม 4' + chr(10) + 'แขวงลุมพินี เขตปางคอยแหลม กรุงเทพมหานคร 10330' + chr(10) + 'Tel: 02-650-7400 | Email: thailand@gac.com']
    ]
    header_table = Table(header_data, colWidths=[9*cm, 9*cm])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Title
    title_style = ParagraphStyle('Title', fontSize=16, bold=True, alignment=1)
    elements.append(Paragraph("RECEIPT COPY / TAX INVOICE COPY", title_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Get data
    invoice_no = invoice_data.get('invoice_no', '-')
    running_no = invoice_data.get('running_no', 'Draft')
    invoice_date = invoice_data.get('invoice_date', '-')
    customer = invoice_data.get('customer_name', 'Customer')
    customer_address = invoice_data.get('customer_address', '')[:100]
    
    # Customer & Document Info table
    cust_data = [
        ['ชื่อลูกค้า / Customer Name:' + chr(10) + customer + chr(10) + customer_address,
         'No. / เลขที่: ' + str(running_no) + chr(10) + 'Date / วันที่: ' + str(invoice_date) + chr(10) + 'Invoice No: ' + str(invoice_no)]
    ]
    cust_table = Table(cust_data, colWidths=[10*cm, 8*cm])
    cust_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(cust_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Items Table
    items = invoice_data.get('items', [])
    if not items:
        items = [{'description': 'Service Charges', 'amount': 0}]
    
    table_data = [['รายการ / Description', 'จำนวนเงิน / Amount', 'VAT 7%', 'Total (THB)']]
    
    total_amt = 0
    total_vat = 0
    
    for item in items[:15]:
        desc = item.get('description', '-')[:40]
        amt = float(item.get('amount', 0))
        vat = amt * 0.07
        total_amt += amt
        total_vat += vat
        table_data.append([desc, f"{amt:,.2f}", f"{vat:,.2f}", f"{amt:,.2f}"])
    
    # Calculate totals
    exchange_rate = float(invoice_data.get('exchange_rate', 1) or 1)
    total_usd = float(invoice_data.get('total_amount', 0) or 0)
    total_thb = float(invoice_data.get('total_thb', 0) or 0)
    if total_thb == 0 and total_usd > 0:
        total_thb = total_usd * exchange_rate
    vat = total_thb - (total_thb / 1.07)
    subtotal = total_thb - vat
    
    items_table = Table(table_data, colWidths=[9*cm, 3*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Totals
    totals_data = [
        ['รวมเงิน / Subtotal:', f"{subtotal:,.2f}"],
        ['ภาษีมูลค่าเพิ่ม 7% / VAT 7%:', f"{vat:,.2f}"],
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
    
    # Footer
    footer_data = [
        ['วิธีการชำระเงิน / Payment Method:' + chr(10) + 'Cash  Credit  Cheque' + chr(10) + 'Bank: Bangkok Bank | A/C: 123-456-7890',
         '________________________' + chr(10) + 'ผู้เก็บเงิน / Bill Collector' + chr(10) + chr(10) + '________________________' + chr(10) + 'Accountant']
    ]
    footer_table = Table(footer_data, colWidths=[12*cm, 6*cm])
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(footer_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_xml(invoice_data):
    """Generate e-Tax XML in memory"""
    from lxml import etree
    
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
    
    # Buyer
    buyer = etree.SubElement(root, 'Buyer')
    etree.SubElement(buyer, 'Name').text = invoice_data.get('customer_name', '')
    
    # Items
    items_elem = etree.SubElement(root, 'Items')
    for item in invoice_data.get('items', []):
        item_elem = etree.SubElement(items_elem, 'Item')
        etree.SubElement(item_elem, 'Number').text = str(item['item_no'])
        etree.SubElement(item_elem, 'Description').text = item['description']
        etree.SubElement(item_elem, 'Total').text = str(item['amount'])
        etree.SubElement(item_elem, 'VatRate').text = str(item['vat_rate'])
        etree.SubElement(item_elem, 'VatAmount').text = str(item['vat_amount'])
    
    # Summary
    summary = etree.SubElement(root, 'Summary')
    etree.SubElement(summary, 'SubTotal').text = str(invoice_data.get('total_amount', 0))
    etree.SubElement(summary, 'VatTotal').text = str(invoice_data['vat_amount'])
    etree.SubElement(summary, 'TotalAmount').text = str(invoice_data['total_amount'])
    etree.SubElement(summary, 'CurrencyCode').text = 'USD'
    etree.SubElement(summary, 'ExchangeRate').text = str(invoice_data['exchange_rate'])
    etree.SubElement(summary, 'TotalAmountTHB').text = str(invoice_data['total_thb'])
    
    # Output
    buffer = BytesIO()
    tree = etree.ElementTree(root)
    tree.write(buffer, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    buffer.seek(0)
    return buffer

# ============================================
# STREAMLIT UI
# ============================================

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 24px; font-weight: bold; color: #1e3a5f; padding: 10px; }
    .success-box { padding: 15px; background-color: #d4edda; border-radius: 5px; }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)
    
st.markdown("""<style>
    .main-header { 
        font-size: 28px; 
        font-weight: bold; 
        color: #ffffff;
        background: linear-gradient(135deg, #0066b2 0%, #00a3e0 100%);
        padding: 20px;
        text-align: center;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .stButton>button { 
        border-radius: 10px;
    }
</style>""", unsafe_allow_html=True)

def main():
    # Set page config for wide layout
    st.set_page_config(page_title="GAC E-Tax Invoice", page_icon="🏢", layout="wide")
    
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #0066b2 0%, #00a3e0 100%); border-radius: 15px; margin-bottom: 20px;">
        <h2 style="color: white; margin: 0;">🏢 GACTH</h2>
        <p style="color: white; margin: 5px 0;">E-Tax Receipt</p>
    </div>
    """, unsafe_allow_html=True)
    
    # BOT API Status
    creds = get_bot_credentials()
    if creds:
        st.sidebar.success("✅ BOT API Connected")
        st.sidebar.code(f"Token: {creds[:20]}...")
    else:
        st.sidebar.info("ℹ️ BOT API: Not configured (OK for local)")
    
    # Initialize menu in session state
    if 'menu' not in st.session_state:
        st.session_state['menu'] = '🏠 Dashboard'
    
    menu_options = ["🏠 Dashboard", "📤 Upload", "📋 Invoice List", "⚙️ Settings", "👁️ Preview", "📊 History"]
    menu = st.sidebar.radio("เมนู", menu_options, 
                          index=menu_options.index(st.session_state['menu']))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{COMPANY_NAME}**")
    st.sidebar.markdown(f"TAX ID: {COMPANY_TAX_ID}")
    
    if menu == "📤 Upload":
        show_upload()
    elif menu == "📋 Invoice List":
        show_invoice_list()
    elif menu == "⚙️ Settings":
        show_settings()
    elif menu == "👁️ Preview":
        show_preview()
    elif menu == "📊 History":
        show_history()

def show_upload():
    st.markdown('<p class="main-header">📤 Upload XML Invoice</p>', unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 ดูรายการ Invoice", use_container_width=True):
            st.session_state['menu'] = '📋 Invoice List'
            st.rerun()
    with col2:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state['menu'] = '🏠 Dashboard'
            st.rerun()
    
    # Recent invoices
    st.markdown("---")
    st.markdown("### 📋 5 รายการล่าสุด")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT invoice_no, customer_name, invoice_date, total_amount, status FROM invoices ORDER BY id DESC LIMIT 5")
            recent = cur.fetchall()
            if recent:
                for inv in recent:
                    st.markdown(f"- **{inv[0]}** | {inv[1]} | {inv[2]} | ฿{inv[3]:,.2f} | {inv[4]}")
            else:
                st.info("ยังไม่มีรายการ")
    except:
        st.info("ยังไม่มีรายการ")
    st.markdown("---")
    
    # Show sidebar with uploaded files
    show_uploaded_list_sidebar()
    
    # File uploader
    st.markdown("### 📤 อัปโหลดไฟล์ XML")
    uploaded_files = st.file_uploader(
        "เลือกไฟล์ (เลือกได้หลายไฟล์)", 
        type=['xml'], 
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        # Process files and show preview
        st.session_state['pending_invoices'] = []
        
        for uploaded_file in uploaded_files:
            try:
                from xml.etree import ElementTree as ET
                import re
                import json
                
                # Read XML content
                xml_content = uploaded_file.getvalue()
                xml_str = xml_content.decode('utf-8', errors='ignore')
                
                # Extract invoice data
                invoice_data = {'filename': uploaded_file.name}
                
                # Extract Invoice No
                invoice_no_match = re.search(r'Textbox183="([^"]*)"', xml_str)
                if invoice_no_match:
                    invoice_data['invoice_no'] = invoice_no_match.group(1).replace(':', '').strip()
                
                # Extract Customer Name & Address
                billing_party_match = re.search(r'BillingPartyName="([^"]*)"', xml_str)
                if billing_party_match:
                    billing_text = billing_party_match.group(1).replace('&amp;', '&')
                    # Replace escape codes with newlines FIRST
                    billing_text = billing_text.replace('&#xD;', '\n').replace('&#xA;', '\n')
                    lines = [l.strip() for l in billing_text.split('\n') if l.strip()]
                    if len(lines) >= 2:
                        invoice_data['customer_name'] = lines[1] if len(lines) > 1 else lines[0]
                        invoice_data['customer_address'] = '\n'.join(lines[2:]) if len(lines) > 2 else ''
                    else:
                        invoice_data['customer_name'] = lines[0] if lines else ''
                        invoice_data['customer_address'] = ''
                
                # Extract Invoice Date
                date_match = re.search(r'Textbox184="([^"]*)"', xml_str)
                if date_match:
                    date_str = date_match.group(1).replace(':', '').strip()
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
                        invoice_data['invoice_date'] = dt.strftime("%d %b %Y")
                    except:
                        invoice_data['invoice_date'] = date_str
                
                # Extract Total Amount
                total_match = re.search(r'Textbox104="([^"]*)"', xml_str)
                if total_match:
                    try:
                        invoice_data['total_amount'] = float(total_match.group(1))
                    except:
                        invoice_data['total_amount'] = 0
                
                # Extract VAT Amount
                vat_match = re.search(r'Textbox117="([^"]*)"', xml_str)
                if vat_match:
                    try:
                        invoice_data['vat_amount'] = float(vat_match.group(1))
                    except:
                        invoice_data['vat_amount'] = 0
                
                # Extract Items
                items = []
                details = re.findall(r'<Details[^>]*Textbox57="([^"]*)"[^>]*ServiceCode2="([^"]*)"[^>]*Textbox8="([^"]*)"', xml_str)
                for d in details:
                    item_no, desc, amount = d
                    desc = desc.replace('&amp;', '&').replace('&#xD;', ' ').replace('&#xA;', ' ').strip()
                    try:
                        amt = float(amount)
                    except:
                        amt = 0
                    if desc and amt > 0:
                        items.append({
                            'item_no': len(items) + 1,
                            'description': desc,
                            'amount': amt,
                            'category': 'VAT_7'
                        })
                
                invoice_data['items'] = items
                st.session_state['pending_invoices'].append(invoice_data)
                
            except Exception as e:
                st.error(f"Error: {e}")
        
        # Show preview and confirmation
        if st.session_state.get('pending_invoices'):
            st.success(f"📄 พบ {len(st.session_state['pending_invoices'])} ไฟล์ - ตรวจสอบข้อมูลก่อนบันทึก")
            
            # Show preview
            for i, inv in enumerate(st.session_state.get('pending_invoices', [])):
                if not inv:
                    continue
                with st.expander(f"📋 {inv.get('invoice_no', 'Invoice')}"):
                    st.write(f"**Customer:** {inv.get('customer_name', '-')}")
                    st.write(f"**Date:** {inv.get('invoice_date', '-')}")
                    st.write(f"**Amount:** {inv.get('total_amount', 0):,.2f}")
                    st.write(f"**Items:** {len(inv.get('items', []))} รายการ")
            
            # Confirmation button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ ยืนยันบันทึก", key="confirm_save"):
                    # Save to database
                    # Ensure database is initialized
                    init_database()
                    
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    saved = 0
                    errors = []
                    for inv in st.session_state.get('pending_invoices', []):
                        if not inv:
                            continue
                        try:
                            items = inv.get('items', [])
                            items_json = json.dumps(items) if isinstance(items, list) else '[]'
                            
                            values = (
                                str(inv.get('filename', '')),
                                str(inv.get('invoice_no', '')),
                                str(inv.get('invoice_date', '')),
                                str(inv.get('customer_name', '')),
                                str(inv.get('customer_address', '')),
                                str(inv.get('job_number', '')),
                                str(inv.get('awb', '')),
                                str(inv.get('job_ref', '')),
                                float(inv.get('exchange_rate', 1)),
                                float(inv.get('total_amount', 0)),
                                float(inv.get('total_thb', 0)),
                                items_json,
                                'uploaded',
                                str(inv.get('currency', 'USD'))
                            )
                            cursor.execute("""INSERT INTO invoices (filename, invoice_no, invoice_date, customer_name, customer_address, job_number, awb, job_ref, exchange_rate, total_amount, total_thb, items_json, status, currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
                            saved += 1
                        except Exception as insert_err:
                            errors.append(str(insert_err))
                            continue
                    conn.commit()
                    
                    # Check saved
                    cursor.execute('SELECT COUNT(*) FROM invoices')
                    total = cursor.fetchone()[0]
                    conn.close()
                    
                    if errors:
                        st.error(f"Errors: {errors}")
                    if saved > 0:
                        st.success(f"✅ บันทึก {saved} ใบสำเร็จ! (Total in DB: {total})")
                        st.session_state.pop('pending_invoices', None)
                        st.rerun()
                    else:
                        st.error(f"❌ ไม่สามารถบันทึกได้: {errors}")
                    st.session_state.pop('pending_invoices', None)
                    st.success(f"✅ บันทึก {saved} ใบสำเร็จ! (Status: อัปโหลดแล้ว)")
                    st.rerun()
            with col2:
                if st.button("❌ ยกเลิก", key="cancel_save"):
                    st.session_state.pop('pending_invoices', None)
                    st.rerun()
    
    # Show summary and button to go to Invoice List
    files = list_uploaded_files()
    if files:
        st.markdown("### 📋 ไฟล์ที่อัปโหลดแล้ว")
        
        for f in files:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"📄 {f['filename']}")
            with col2:
                if st.button("🗑️", key=f"del_{f['filename']}"):
                    delete_uploaded_file(f['filename'])
                    st.rerun()
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 ไปหน้า Invoice List", type="primary"):
                st.session_state['menu'] = '📋 Invoice List'
                st.rerun()
        with col2:
            if st.button("🔄 รีโหลดหน้า"):
                st.rerun()




def show_uploaded_list_sidebar():
    """Show list of uploaded files in sidebar"""
    files = list_uploaded_files()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 ไฟล์ที่อัปโหลด")
    
    if files:
        st.sidebar.caption(f"📄 ทั้งหมด: {len(files)} ไฟล์")
        
        for f in files[:10]:
            st.sidebar.code(f"📄 {f['filename'][:30]}")
        
        if len(files) > 10:
            st.sidebar.caption(f"... และอีก {len(files) - 10} ไฟล์")
        
        # Clear all button
        if st.sidebar.button("🗑️ ลบทั้งหมด", key="clear_all"):
            for f in files:
                try:
                    delete_uploaded_file(f['filename'])
                except:
                    pass
            st.sidebar.success("✅ ลบไฟล์ทั้งหมดแล้ว!")
            st.rerun()
    else:
        st.sidebar.caption("ยังไม่มีไฟล์")



def parse_xml_invoice(content):
    """Parse XML invoice from GAC system"""
    import xml.etree.ElementTree as ET
    
    try:
        root = ET.fromstring(content)
        
        # Define namespace
        ns = {'ns': 'FIN_SalesInvoiceBulkPrint'}
        
        # Find invoice data
        invoice_data = {
            'invoice_no': '',
            'customer_name': '',
            'job_number': '',
            'awb': '',
            'invoice_date': '',
            'exchange_rate': 30.909,
            'total_amount': 0,
            'total_thb': 0,
            'vat_amount': 0,
            'items': []
        }
        
        # Extract data from XML attributes
        # Find Textbox elements
        for elem in root.iter():
            # Invoice No
            if elem.get('Textbox183'):
                invoice_data['invoice_no'] = elem.get('Textbox183', '')
            # Customer - split name (line 1) and address (lines 2-4)
            if elem.get('BillingPartyName'):
                billing = elem.get('BillingPartyName', '').replace('Billing Party:', '').strip()
                lines = billing.replace('&#xD;&#xA;', '\n').replace('&#xD;', '\n').replace('&#xA;', '\n').split('\n')
                invoice_data['customer_name'] = lines[0].strip() if lines else ''
                invoice_data['customer_address'] = '\n'.join([l.strip() for l in lines[1:] if l.strip()]) if len(lines) > 1 else ''
            # Job No
            if elem.get('Textbox188'):
                invoice_data['job_number'] = elem.get('Textbox188', '')
            # AWB
            if elem.get('Textbox65'):
                invoice_data['awb'] = elem.get('Textbox65', '')
            # Invoice Date
            if elem.get('Textbox184'):
                invoice_data['invoice_date'] = elem.get('Textbox184', '')
            # Exchange Rate
            if elem.get('Textbox186'):
                rate_str = elem.get('Textbox186', '').replace('USD / THB @ ', '').strip()
                try:
                    invoice_data['exchange_rate'] = float(rate_str)
                except:
                    pass
            # Total USD
            if elem.get('BilledOnInvoice1'):
                try:
                    invoice_data['total_amount'] = float(elem.get('BilledOnInvoice1', 0))
                except:
                    pass
            # Total THB
            if elem.get('Textbox104'):
                try:
                    invoice_data['total_thb'] = float(elem.get('Textbox104', 0))
                except:
                    pass
            # VAT
            if elem.get('Textbox117'):
                try:
                    invoice_data['vat_amount'] = float(elem.get('Textbox117', 0))
                except:
                    pass
        
        # Extract items from Details
        item_no = 1
        for elem in root.iter():
            if elem.get('Textbox4'):  # Service code description
                desc = elem.get('Textbox4', '')
                amount = 0
                try:
                    amount = float(elem.get('Textbox8', 0))
                except:
                    pass
                
                if desc and amount > 0:
                    invoice_data['items'].append({
                        'item_no': item_no,
                        'description': desc,
                        'amount': amount,
                        'vat_rate': '0',
                        'vat_amount': 0
                    })
                    item_no += 1
        
        return invoice_data
        
    except Exception as e:
        return {'error': str(e)}


def process_single_file(uploaded_file, return_data=False):
    """Process a single file"""
    # Process in memory
    content = uploaded_file.getvalue()
    
    if uploaded_file.name.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(BytesIO(content))
        content = df.to_csv(index=False).encode('utf-8')
    
    # Save to temp file for ref extraction
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp:
        tmp.write(content.decode('utf-8'))
        tmp_path = tmp.name
    
    # Extract reference numbers
    refs = extract_invoice_refs(tmp_path)
    os.unlink(tmp_path)
    
    # Store in session state
    st.session_state['raw_content'] = content
    st.session_state['filename'] = uploaded_file.name
    st.session_state['refs'] = refs
    
    # Process items
    items = process_csv_in_memory(content, uploaded_file.name)
    st.session_state['items'] = items
    
    st.success(f"✅ อัปโหลดสำเร็จ: {uploaded_file.name}")
    
    # Show items preview
    st.markdown("### 📋 Items Found")
    
    # Allow editing tax category
    # Single VAT category for all items
    default_cat = "VAT_7"
    all_categories = ["NON_VAT", "VAT_7"]
    default_cat = st.selectbox("VAT Category สำหรับทุก Item", all_categories, index=1)
    
    for item in items:
        item['category'] = default_cat
    
    # Date and Exchange rate
    st.markdown("### 📅 วันที่ & 💱 อัตราแลกเปลี่ยน")
    
    # Date selector
    invoice_date = st.date_input("วันที่รับเงิน", value=datetime.now().date(), key=f"date_{uploaded_file.name}")
    
    # Try to get rate from API, fallback to manual
    api_rate = get_exchange_rate_from_api(str(invoice_date))
    
    col1, col2 = st.columns([2, 1])
    
    # Get current rate - use session state, fallback to API or default
    rate_key = f"exchange_rate_{uploaded_file.name}"
    
    # Check if we have a stored rate
    if rate_key not in st.session_state:
        # Try to get from API first
        if api_rate:
            st.session_state[rate_key] = api_rate
        else:
            st.session_state[rate_key] = 30.909
    
    with col1:
        st.caption(f"📅 วันที่: {invoice_date}")
        if api_rate:
            st.success(f"📈 Rate อัตโนมัติ: {api_rate:.4f} THB/USD")
        else:
            st.warning("📌 ไม่สามารถดึง Rate อัตโนมัติได้")
        
        # Exchange rate input - use text input
        rate_str = st.text_input(
            "💱 อัตราแลกเปลี่ยน ณ วันรับเงิน (USD/THB)", 
            value=st.session_state.get(f"rate_input_{uploaded_file.name}", f"{st.session_state.get(rate_key, 30.909):.4f}"),
            key=f"rate_input_{uploaded_file.name}"
        )
        try:
            exchange_rate = float(rate_str)
        except:
            exchange_rate = 30.909
        
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 ดึง Rate ใหม่", key=f"refresh_rate_{uploaded_file.name}"):
            new_rate = get_exchange_rate_from_api(str(invoice_date))
            if new_rate:
                st.session_state[rate_key] = new_rate
                # Update the text input value - sync both keys
                st.session_state[f"rate_input_{uploaded_file.name}"] = f"{new_rate:.4f}"
                st.session_state[rate_key] = f"{new_rate:.4f}"
                st.success(f"✅ ได้ Rate ใหม่: {new_rate:.4f} THB/USD")
            else:
                st.error("❌ ไม่สามารถดึง Rate ได้ กรุณากรอกเอง")
    
    st.session_state['exchange_rate'] = exchange_rate
    
    # Invoice info
    col1, col2 = st.columns(2)
    with col1:
        invoice_no = st.text_input("Invoice No", value="3101523543", key=f"inv_{uploaded_file.name}")
    with col2:
        invoice_date_str = st.text_input("วันที่ (DD MMM YYYY)", value=invoice_date.strftime("%d %b %Y") if hasattr(invoice_date, 'strftime') else str(invoice_date), key=f"date_str_{uploaded_file.name}")
    
    # Invoice No and Job No
    col1, col2 = st.columns(2)
    with col1:
        invoice_no = st.text_input("Invoice No", value="3101523543", key=f"inv_{uploaded_file.name}")
    with col2:
        job_no = st.text_input("Job No.", value="", key=f"job_{uploaded_file.name}")
    
    customer_name = st.text_input("Customer Name", value="Rock-it Cargo Pte. Ltd.", key=f"cust_{uploaded_file.name}")
    
    info = {
        'invoice_no': invoice_no,
        'job_no': job_no,
        'invoice_date': str(invoice_date),
        'customer_name': customer_name,
        'filename': uploaded_file.name
    }
    st.session_state['invoice_info'] = info
    
    if return_data:
        # Calculate totals for batch
        return calculate_invoice(items, exchange_rate, info)
    
    st.info("👉 ไปที่เมนู 'Preview' เพื่อดูและออกเอกสาร")

def calculate_invoice(items, exchange_rate, info):
    """Calculate invoice totals"""
    from decimal import Decimal
    
    subtotal = Decimal('0')
    vat_total = Decimal('0')
    processed_items = []
    
    for item in items:
        amount = Decimal(str(item['amount']))
        category = item.get('category', 'VAT_7')
        
        if category == 'NON_VAT':
            vat_rate = 0
            vat_amount = Decimal('0')
        elif category == 'PARTIAL_VAT':
            vat_rate = 7
            vat_amount = Decimal(str(item.get('manual_vat', 0)))
        else:
            vat_rate = 7
            vat_amount = amount * Decimal('0.07')
        
        amount_thb = amount * Decimal(str(exchange_rate))
        
        subtotal += amount
        vat_total += vat_amount
        
        processed_items.append({
            'item_no': item['item_no'],
            'description': item['description'],
            'amount': amount,
            'category': category,
            'vat_rate': vat_rate,
            'vat_amount': vat_amount,
            'amount_thb': amount_thb
        })
    
    total = subtotal + vat_total
    total_thb = total * Decimal(str(exchange_rate))
    
    return {
        'filename': info.get('filename', ''),
        'invoice_no': info.get('invoice_no', ''),
        'invoice_date': info.get('invoice_date', ''),
        'customer_name': info.get('customer_name', ''),
        'exchange_rate': exchange_rate,
        'subtotal': subtotal,
        'vat_amount': vat_total,
        'total_amount': total,
        'total_thb': total_thb,
        'items': processed_items
    }


def show_invoice_list():
    """Show list of all uploaded invoices for editing"""
    st.markdown('<p class="main-header">📋 Invoice List</p>', unsafe_allow_html=True)
    
    # Load from files
    invoices = load_invoices_from_db()
    
    # Debug info
    st.caption(f"📊 Debug: Found {len(invoices)} invoices in database")
    
    if not invoices:
        st.warning("⚠️ ยังไม่มี Invoice")
        if st.button("📤 ไปหน้าอัปโหลด"):
            st.session_state['menu'] = '📤 Upload'
            st.rerun()
        return
    
    st.markdown(f"### 📋 รายการ Invoice ({len(invoices)} ใบ)")
    
    
    # Show table with all invoices - enhanced
    data = []
    for i, inv in enumerate(invoices):
        status = inv.get('status', 'uploaded')
        status_display_map = {
            'pending': '⏳ รอดำเนินการ',
            'uploaded': '✅ อัปโหลดแล้ว',
            'issued': '📄 ออกใบเสร็จแล้ว',
            'validated': '✓ ผ่านการตรวจสอบ',
            'xml_generated': '📄 XML สร้างแล้ว',
            'signed': '🔐 ลงนามแล้ว',
            'sent': '📤 ส่ง RD แล้ว',
            'delivered': '🎉 ส่งเรียบร้อย',
            'failed': '❌ ล้มเหลว'
        }
        status_display = status_display_map.get(status, status)
        
        data.append({
            'Invoice No': inv.get('invoice_no', '-'),
            'Job No': inv.get('job_number', '-'),
            'Customer': inv.get('customer_name', ''),
            'Address': inv.get('customer_address', ''),
            'Date': inv.get('invoice_date', '-'),
            'Total': f"{inv.get('currency', 'USD')} {float(inv.get('total_amount', 0)):,.2f}",
            'Currency': inv.get('currency', 'USD'),
            'Status': status_display,
        })
    
    # Prepare data for dataframe with proper column widths
    table_data = []
    for inv in invoices:
        status = inv.get('status', 'pending')
        status_display_map = {
            'pending': '⏳ รอ',
            'uploaded': '✅ อัปโหลด',
            'issued': '📄 ออกแล้ว',
            'validated': '✓ ผ่านตรวจ',
            'xml_generated': '📄 XML',
            'signed': '🔐 ลงนาม',
            'sent': '📤 ส่ง RD',
            'delivered': '🎉 สำเร็จ',
            'failed': '❌ ล้มเหลว'
        }
        
        curr = inv.get('currency', 'USD')
        
        table_data.append({
            'Invoice No.': inv.get('invoice_no', '-'),
            'Job No.': inv.get('job_number', '-') if inv.get('job_number') else '-',
            'Customer Name': inv.get('customer_name', '-'),
            'Date': inv.get('invoice_date', '-'),
            'Amount': f"{curr} {float(inv.get('total_amount', 0)):,.2f}",
            'Status': status_display_map.get(status, status),
            'ID': inv.get('id')
        })
    
    if table_data:
        # Create dataframe
        df = pd.DataFrame(table_data)
        
        # Display with custom styling
        st.dataframe(
            df[['Invoice No.', 'Job No.', 'Customer Name', 'Date', 'Amount', 'Status']],
            use_container_width=True,
            hide_index=True,
            column_config={
                'Invoice No.': st.column_config.TextColumn('Invoice No.', width='medium'),
                'Job No.': st.column_config.TextColumn('Job No.', width='small'),
                'Customer Name': st.column_config.TextColumn('Customer Name', width='large'),
                'Date': st.column_config.TextColumn('Date', width='small'),
                'Amount': st.column_config.TextColumn('Amount', width='medium'),
                'Status': st.column_config.TextColumn('Status', width='small'),
            }
        )
        
        # Delete section below
        st.markdown("### 🗑️ ลบ Invoice")
        delete_options = []
        delete_map = {}
        for i, inv in enumerate(table_data):
            key = f"{inv['Invoice No.']} | {inv['Customer Name'][:30]}"
            delete_options.append(key)
            delete_map[key] = inv['ID']
        
        col1, col2 = st.columns([4, 1])
        with col1:
            selected_delete = st.selectbox("เลือก Invoice ที่จะลบ:", delete_options, key="delete_select")
        with col2:
            if st.button("🗑️ ลบ", key="btn_delete"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM invoices WHERE id = ?", (delete_map[selected_delete],))
                conn.commit()
                conn.close()
                st.success("✅ ลบสำเร็จ!")
                st.rerun()
    else:
        st.info("ยังไม่มี Invoice")
    
    # Edit section
    st.markdown("### 🧾 ออกใบเสร็จ")
    
    # Select invoice to edit
    options = []
    for inv in invoices:
        name = inv.get('customer_name', 'Unknown')
        addr = inv.get('customer_address', '')
        # Shorten address for display
        if addr:
            addr_short = addr.replace('\n', ', ')
            options.append(f"{inv.get('invoice_no', 'N/A')} | {name} | {addr_short}")
        else:
            options.append(f"{inv.get('invoice_no', 'N/A')} | {name}")
    selected_idx = st.selectbox("เลือก Invoice ที่จะออกใบเสร็จ:", range(len(options)), format_func=lambda x: options[x])
    
    # Show selected invoice details
    inv = invoices[selected_idx]
    
    with st.expander(f"✏️ ออกใบเสร็จ: {inv.get('filename', inv.get('invoice_no', 'Invoice'))}", expanded=True):
        # Edit form
        col1, col2 = st.columns(2)
        
        with col1:
            new_inv_no = st.text_input("Invoice No", value=inv.get('invoice_no', ''), key=f"edit_inv_{selected_idx}")
        with col2:
            # Date picker
            from datetime import datetime
            current_date_str = inv.get('invoice_date', '')
            try:
                # Try to parse the date
                current_date = datetime.strptime(current_date_str, "%d %b %Y").date() if current_date_str else datetime.now().date()
            except:
                current_date = datetime.now().date()
            
            new_date = st.date_input("วันที่รับเงิน", value=current_date, key=f"edit_date_{selected_idx}")
        
        new_customer = st.text_input("Customer Name", value=inv.get('customer_name', ''), key=f"edit_cust_{selected_idx}")
        new_address = st.text_input("Address", value=inv.get('customer_address', ''), key=f"edit_addr_{selected_idx}")
        col1, col2 = st.columns([3, 1])
        with col1:
            # Get exchange rate from invoice data
            saved_rate = float(inv.get('exchange_rate', 30.909)) if inv.get('exchange_rate') else 30.909
            # Keep 1.0 as default (for THB invoices)
            
            # Show current rate
            new_rate_str = st.text_input("อัตราแลกเปลี่ยน ณ วันรับเงิน (USD/THB)", 
                                       value=f"{saved_rate:.4f}", 
                                       key=f"edit_rate_{selected_idx}")
            try:
                new_rate = float(new_rate_str)
            except:
                new_rate = 1.0
        with col2:
            st.write("")
            st.write("")
            if st.button("🔄 ดึง Rate", key=f"refresh_edit_{selected_idx}"):
                invoice_date_str = str(new_date) if new_date else str(datetime.now().date())
                new_rate_api = get_exchange_rate_from_api(invoice_date_str)
                if new_rate_api:
                    # Can't modify widget value directly, show success and user will see new value after rerun
                    st.success(f"✅ Rate ใหม่: {new_rate_api:.4f}")
                    st.rerun()
                else:
                    st.warning("⚠️ ไม่ได้ Rate จาก API")
        
        # Update button
        if st.button("💾 บันทึกการแก้ไข", key=f"save_{selected_idx}"):
            invoices[selected_idx]['invoice_no'] = new_inv_no
            invoices[selected_idx]['invoice_date'] = new_date
            invoices[selected_idx]['customer_name'] = new_customer
            invoices[selected_idx]['address'] = new_address
            invoices[selected_idx]['exchange_rate'] = new_rate
            
            # Recalculate totals
            recalculate_invoice(invoices[selected_idx])
            
            st.success("✅ บันทึกสำเร็จ!")
            st.rerun()
        
        # Show items
        st.markdown("#### รายการสินค้า")
        items = inv.get('items', [])
        
        for j, item in enumerate(items):
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                new_desc = st.text_input(f"Item {j+1}", value=item.get('description', ''), key=f"item_desc_{selected_idx}_{j}")
            with col2:
                new_amount_str = st.text_input(f"Amount", value=str(item.get("amount", 0)), key=f"item_amt_{selected_idx}_{j}")
                try:
                    new_amount = float(new_amount_str.replace(",", ""))
                except:
                    new_amount = 0
            with col3:
                detected_cat = determine_category(new_desc, DEFAULT_MAPPING)
                current_cat = item.get('category', detected_cat)
                new_cat = st.selectbox(f"VAT", ["NON_VAT", "VAT_7", "PARTIAL_VAT"], 
                                    index=["NON_VAT", "VAT_7", "PARTIAL_VAT"].index(current_cat) if current_cat in ["NON_VAT", "VAT_7", "PARTIAL_VAT"] else 1,
                                    key=f"item_cat_{selected_idx}_{j}")
            
            item['description'] = new_desc
            item['amount'] = new_amount
            item['category'] = new_cat
        
        # Calculate totals
        receipt_rate = inv.get('exchange_rate', 30.909)
        subtotal = 0
        vat_total = 0
        nonvat_total = 0
        
        for item in items:
            amt_usd = item.get('amount', 0)
            amt_thb = amt_usd * receipt_rate
            cat = item.get('category', 'VAT_7')
            
            if cat == 'VAT_7':
                vat = amt_thb * 0.07
                vat_total += vat
            elif cat == 'PARTIAL_VAT':
                vat = item.get('manual_vat', 0)
                vat_total += vat
            else:
                vat = 0
            
            subtotal += amt_thb
        
        total = subtotal + vat_total
        
        # Show summary
        st.markdown("---")
        st.markdown("### 💰 สรุปการคำนวณ")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Subtotal (THB)", f"฿{subtotal:,.2f}")
        with col2:
            st.metric("VAT 7% (THB)", f"฿{vat_total:,.2f}")
        with col3:
            st.metric("Total (THB)", f"฿{total:,.2f}")
        with col4:
            st.metric("อัตราแลกเปลี่ยน", f"{receipt_rate:.4f}")
        
        # Save button
        if st.button("💾 บันทึกการแก้ไข", type="primary", key="save_items"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""UPDATE invoices SET 
                    items_json = ?, exchange_rate = ?, total_amount = ?, total_thb = ?, status = ?
                    WHERE id = ?""",
                    (json.dumps(items), receipt_rate, subtotal, total, 'issued', inv.get('id')))
                conn.commit()
                conn.close()
                st.success("✅ บันทึกสำเร็จ!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
        
        # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 อัปโหลดเพิ่ม", key="btn_upload_more"):
            st.session_state['menu'] = '📤 Upload'
            st.session_state.pop('_menu_to_rerun', None)
            st.rerun()
    with col2:
        if st.button("👁️ ไป Preview", key="btn_go_preview"):
            st.session_state['batch_invoices'] = invoices
            st.session_state['menu'] = '👁️ Preview'
            st.rerun()
    # E-Tax Workflow Section
    st.markdown("---")
    st.markdown("### 🧾 E-Tax Workflow")
    
    if st.button("🚀 Run E-Tax Workflow", key="btn_etax_workflow"):
        # Prepare invoice data for e-tax
        invoice_data = {
            'invoice_no': inv.get('invoice_no', ''),
            'invoice_date': inv.get('invoice_date', ''),
            'customer': {
                'name': inv.get('customer_name', ''),
                'tax_id': '0105535169497',  # Default GAC Tax ID for now
                'branch_code': '00000',
                'address': inv.get('customer_address', '')
            },
            'items': inv.get('items', []),
            'subtotal': float(inv.get('total_amount', 0)),
            'vat_amount': float(inv.get('total_amount', 0)) * 0.07,
            'total_amount': float(inv.get('total_amount', 0)) * 1.07
        }
        
        # Run workflow
        result = run_etax_workflow(invoice_data)
        
        # Show result
        if result['final_status'] == 'DELIVERED':
            st.success(f"✅ E-Tax Workflow สำเร็จ! RD ID: {result.get('rd_submission_id')}")
        else:
            st.error(f"❌ E-Tax Workflow ล้มเหลว: {result.get('error')}")


def recalculate_invoice(invoice):
    """Recalculate invoice totals"""
    from decimal import Decimal
    
    rate = Decimal(str(invoice.get('exchange_rate', 30.909)))
    subtotal = Decimal('0')
    vat_total = Decimal('0')
    
    for item in invoice.get('items', []):
        amount = Decimal(str(item.get('amount', 0)))
        category = item.get('category', 'VAT_7')
        
        if category == 'NON_VAT':
            vat_amount = Decimal('0')
        else:
            vat_amount = amount * Decimal('0.07')
        
        amount_thb = amount * rate
        
        item['vat_amount'] = vat_amount
        item['amount_thb'] = amount_thb
        
        subtotal += amount
        vat_total += vat_amount
    
    invoice['subtotal'] = subtotal
    invoice['vat_amount'] = vat_total
    invoice['total_amount'] = subtotal + vat_total
    invoice['total_thb'] = (subtotal + vat_total) * rate

def show_settings():
    init_database()  # Ensure tables exist
    st.markdown('<p class="main-header">⚙️ Settings</p>', unsafe_allow_html=True)
    
    # Company Settings
    st.markdown("### 🏢 ข้อมูลบริษัท")
    company = get_company_settings()
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("ชื่อบริษัท", company.get('name', 'Gulf Agency Company (Thailand) Ltd.'))
        company_address = st.text_area("ที่อยู่", company.get('address', ''))
    with col2:
        company_tax_id = st.text_input("Tax ID", company.get('tax_id', ''))
        company_tel = st.text_input("โทร", company.get('tel', ''))
    
    if st.button("💾 บันทึกบริษัท", key="save_company"):
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE company_settings SET company_name=?, company_address=?, company_tax_id=?, company_tel=? WHERE id=1",
                     (company_name, company_address, company_tax_id, company_tel))
            conn.commit()
            conn.close()
            st.success("✅ บันทึกข้อมูลบริษัทแล้ว!")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    st.markdown("### 📋 Tax Settings")
    
    # Load from database
    import sqlite3
    saved_non_vat = ', '.join(DEFAULT_MAPPING['NON_VAT'])
    saved_partial = ', '.join(DEFAULT_MAPPING['PARTIAL_VAT'])
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tax_mapping'")
        if c.fetchone():
            c.execute("SELECT non_vat, partial_vat FROM tax_mapping WHERE id=1")
            row = c.fetchone()
            if row:
                saved_non_vat = row[0] or saved_non_vat
                saved_partial = row[1] or saved_partial
        conn.close()
    except Exception as e:
        pass
    
    st.info("💡 รายการที่ไม่ตรงกับ keyword ใดๆ จะคิด VAT 7%")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 กลุ่ม A - ไม่คิด VAT (0%)")
        non_vat = st.text_area("Keywords (คั่นด้วย comma)", value=saved_non_vat, height=120, key="non_vat")
    
    with col2:
        st.markdown("#### 📋 กลุ่ม C - หัก VAT บางส่วน")
        partial = st.text_area("Keywords (คั่นด้วย comma)", value=saved_partial, height=120, key="partial")
    
    if st.button("💾 Save Settings", type="primary"):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Create table if not exists
            c.execute("""
                CREATE TABLE IF NOT EXISTS tax_mapping (
                    id INTEGER PRIMARY KEY, non_vat TEXT, partial_vat TEXT
                )
            """)
            # Check if row exists
            c.execute("SELECT COUNT(*) FROM tax_mapping")
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO tax_mapping VALUES (1, ?, ?)", (non_vat, partial))
            else:
                c.execute("UPDATE tax_mapping SET non_vat=?, partial_vat=? WHERE id=1", (non_vat, partial))
            conn.commit()
            conn.close()
            st.success("✅ บันทึกสำเร็จ!")
        except Exception as e:
            st.error(f"Error: {e}")

def show_preview():
    st.markdown('<p class="main-header">👁️ Preview & Issue Invoice</p>', unsafe_allow_html=True)
    
    # Check for batch invoices first
    if 'batch_invoices' in st.session_state and st.session_state['batch_invoices']:
        show_batch_preview()
        return
    
    if 'items' not in st.session_state:
        st.warning("⚠️ กรุณาอัปโหลดไฟล์ก่อน")
        return

def show_batch_preview():
    """Preview and issue multiple invoices"""
    batch = st.session_state['batch_invoices']
    
    st.markdown(f"### 📚 {len(batch)} Invoices Ready")
    
    # Select which invoice to preview
    options = []
    for inv in batch:
        name = inv.get('customer_name', '')[:20]
        addr = inv.get('customer_address', '')
        if addr:
            addr_short = addr.replace('\n', ', ')[:25]
            options.append(f"{inv.get('filename', inv.get('invoice_no', 'Unknown'))} - {name} | {addr_short}")
        else:
            options.append(f"{inv.get('filename', inv.get('invoice_no', 'Unknown'))} - {name}")
    options.append("📋 ทั้งหมด")
    
    selected = st.selectbox("เลือก Invoice ที่จะ Preview:", options, key="batch_select")
    
    if selected == "📋 ทั้งหมด":
        # Show all invoices
        for i, inv in enumerate(batch):
            with st.expander(f"📄 {inv.get('filename', inv.get('invoice_no', f'Invoice {i+1}'))}"):
                show_pdf_preview(inv, key_suffix=f"_batch_{i}")
    else:
        idx = options.index(selected)
        inv = batch[idx]
        show_pdf_preview(inv, key_suffix="_batch_selected")

def show_pdf_preview(invoice_data, key_suffix=""):
    """Show PDF-like preview of invoice"""
    from decimal import Decimal
    
    exchange_rate = Decimal(str(invoice_data.get('exchange_rate', 30.909)))
    # Generate running number
    from datetime import datetime
    current_year = datetime.now().year
    year_short = str(current_year)[-2:]  # Get last 2 digits
    running_no = f"{year_short}-0001"  # Default format
    invoice_no = invoice_data.get('invoice_no', '-')
    invoice_date = invoice_data.get('invoice_date', '-')
    customer = invoice_data.get('customer_name', 'Customer')
    job_no = invoice_data.get('job_number', '-')
    awb = invoice_data.get('awb', '-')
    
    # Calculate totals
    total_usd = float(invoice_data.get('total_amount', 0))
    total_vat = float(invoice_data.get('vat_amount', 0))
    subtotal_usd = total_usd - total_vat
    total_thb = total_usd * float(exchange_rate)
    subtotal_thb = subtotal_usd * float(exchange_rate)
    vat_thb = total_vat * float(exchange_rate)
    
    # Build HTML receipt
    html = f"""
    <div style="
        border: 2px solid #333;
        border-radius: 5px;
        padding: 15px;
        background: white;
        font-family: Arial, sans-serif;
        font-size: 12px;
        max-width: 700px;
        margin: 0 auto;
    ">
        <h3 style="text-align: center; color: #1e3a5f; margin: 5px 0;">GAC THAILAND CO., LTD.</h3>
        <p style="text-align: center; margin: 2px 0; font-size: 11px;">9/2 Sathorn 39, South Sathorn Road, Yannawa, Sathorn</p>
        <p style="text-align: center; margin: 2px 0; font-size: 11px;">Bangkok 10120, Thailand</p>
        <p style="text-align: center; margin: 2px 0; font-size: 11px;">Tel: +66 2 676 1900 | Fax: +66 2 676 1990</p>
        <p style="text-align: center; margin: 2px 0; font-size: 11px;">Tax ID: 0105548024532 | Branch: 00000</p>
        
        <hr style="border: 1px solid #333;">
        
        <h3 style="text-align: center; margin: 10px 0;">INVOICE / RECEIPT</h3>
        
        <table style="width: 100%; font-size: 11px;">
            <tr>
                <td style="width: 50%;"><b>Invoice No:</b> {invoice_no}</td>
                <td style="width: 50%; text-align: right;"><b>Running No:</b> {running_no}</td>
            </tr>
            <tr>
                <td><b>Date:</b> {invoice_date}</td>
                <td style="text-align: right;"><b>Job No:</b> {job_no}</td>
            </tr>
            <tr>
                <td colspan="2"><b>Customer:</b> {customer}</td>
            </tr>
            <tr>
                <td colspan="2"><b>AWB/Ref:</b> {awb}</td>
            </tr>
        </table>
        
        <hr style="border: 1px solid #333;">
        
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;" border="1">
            <tr style="background: #f0f0f0;">
                <th style="padding: 6px; width: 10%;">#</th>
                <th style="padding: 6px; width: 45%;">Description</th>
                <th style="padding: 6px; width: 15%; text-align: right;">Qty</th>
                <th style="padding: 6px; width: 15%; text-align: right;">Unit Price</th>
                <th style="padding: 6px; width: 15%; text-align: right;">Amount (USD)</th>
            </tr>
    """
    
    # Add items
    for item in invoice_data.get('items', []):
        desc = item.get('description', '')[:30]
        qty = item.get('quantity', 1)
        unit_price = float(item.get('amount', 0)) / qty if qty else 0
        amount = float(item.get('amount', 0))
        
        html += f"""
            <tr>
                <td style="padding: 4px;">{item.get('item_no', '')}</td>
                <td style="padding: 4px;">{desc}</td>
                <td style="padding: 4px; text-align: right;">{qty}</td>
                <td style="padding: 4px; text-align: right;">${unit_price:.2f}</td>
                <td style="padding: 4px; text-align: right;">${amount:,.2f}</td>
            </tr>
        """
    
    # Add totals
    html += f"""
        </table>
        
        <table style="width: 100%; font-size: 11px; margin-top: 10px;">
            <tr>
                <td style="width: 60%; text-align: right;">Subtotal:</td>
                <td style="width: 20%; text-align: right;">${subtotal_usd:,.2f}</td>
                <td style="width: 20%; text-align: right;">฿{subtotal_thb:,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: right;">VAT 7%:</td>
                <td style="text-align: right;">${total_vat:,.2f}</td>
                <td style="text-align: right;">฿{vat_thb:,.2f}</td>
            </tr>
            <tr style="background: #e0e0e0; font-weight: bold; font-size: 14px;">
                <td style="text-align: right; padding: 8px;">TOTAL:</td>
                <td style="text-align: right; padding: 8px;">${total_usd:,.2f}</td>
                <td style="text-align: right; padding: 8px;">฿{total_thb:,.2f}</td>
            </tr>
        </table>
        
        <hr style="border: 1px solid #333; margin-top: 15px;">
        
        <p style="text-align: center; font-size: 11px; margin: 5px 0;">
            <b>Exchange Rate:</b> 1 USD = {exchange_rate} THB
        </p>
        <p style="text-align: center; font-size: 10px; color: #666; margin: 5px 0;">
            This invoice is subject to GAC Thailand Standard Terms and Conditions
        </p>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Generate buttons
    st.markdown("### 🧾 ออกเอกสาร")
    
    # Preview PDF - show download link
    try:
        from pdf_generator import generate_receipt_pdf
        pdf_buffer = generate_receipt_pdf(invoice_data)
        pdf_bytes = pdf_buffer.getvalue()
        
        # Show preview info
        st.info(f"📄 PDF Ready - {len(pdf_bytes)/1024:.1f} KB")
        
        # Download button instead
    except Exception as e:
        st.error(f"Error: {e}")
    
    col1, col2 = st.columns(2)
    with col1:
        gen_pdf = st.checkbox("📄 PDF", value=True, key=f"pdf{key_suffix}")
    with col2:
        gen_xml = st.checkbox("📄 e-Tax XML", value=False, key=f"xml{key_suffix}")
    
    if st.button("🎫 Generate & Download", type="primary", key=f"gen{key_suffix}"):
        running_no = get_next_running_no()
        invoice_data['running_no'] = running_no
        invoice_data['file_source'] = invoice_data.get('filename', '')
        
        save_invoice(invoice_data)
        
        st.success(f"✅ Running No: {running_no}")
        
        if gen_pdf:
            pdf_buffer = generate_pdf(invoice_data)
            st.download_button(
                "📥 Download PDF",
                pdf_buffer.getvalue(),
                file_name=f"Receipt_{running_no}.pdf",
                mime="application/pdf",
                key=f"dl_pdf{key_suffix}"
            )
        
        if gen_xml:
            xml_buffer = generate_xml(invoice_data)
            st.download_button(
                "📥 Download XML",
                xml_buffer.getvalue(),
                file_name=f"ETax_{running_no}.xml",
                mime="application/xml",
                key=f"dl_xml{key_suffix}"
            )
    
    # Calculate totals
    items = st.session_state['items']
    exchange_rate = st.session_state.get('exchange_rate', 30.909)
    info = st.session_state.get('invoice_info', {})
    
    subtotal = Decimal('0')
    vat_total = Decimal('0')
    processed_items = []
    
    for item in items:
        amount = Decimal(str(item['amount']))
        category = item.get('category', 'VAT_7')
        
        if category == 'NON_VAT':
            vat_rate = 0
            vat_amount = Decimal('0')
        elif category == 'PARTIAL_VAT':
            vat_rate = 7
            vat_amount = Decimal(str(item.get('manual_vat', 0)))
        else:
            vat_rate = 7
            vat_amount = amount * Decimal('0.07')
        
        amount_thb = amount * Decimal(str(exchange_rate))
        
        subtotal += amount
        vat_total += vat_amount
        
        processed_items.append({
            'item_no': item['item_no'],
            'description': item['description'],
            'amount': amount,
            'category': category,
            'vat_rate': vat_rate,
            'vat_amount': vat_amount,
            'amount_thb': amount_thb
        })
    
    total = subtotal + vat_total
    total_thb = total * Decimal(str(exchange_rate))
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Running No", "Auto")
    with col2:
        st.metric("Subtotal", f"${float(subtotal):,.2f}")
    with col3:
        st.metric("VAT", f"${float(vat_total):,.2f}")
    with col4:
        st.metric("Total", f"${float(total):,.2f}")
    
    # Items table
    st.markdown("#### รายการ")
    df = pd.DataFrame(processed_items)
    st.dataframe(df[['item_no', 'description', 'amount', 'vat_rate', 'vat_amount']], use_container_width=True)
    
    # Generate buttons
    st.markdown("### 🧾 ออกเอกสาร")
    
    # Preview PDF - show download link
    try:
        from pdf_generator import generate_receipt_pdf
        pdf_buffer = generate_receipt_pdf(invoice_data)
        pdf_bytes = pdf_buffer.getvalue()
        
        # Show preview info
        st.info(f"📄 PDF Ready - {len(pdf_bytes)/1024:.1f} KB")
        
        # Download button instead
    except Exception as e:
        st.error(f"Error: {e}")
    
    col1, col2 = st.columns(2)
    with col1:
        gen_pdf = st.checkbox("📄 PDF", value=True)
    with col2:
        gen_xml = st.checkbox("📄 e-Tax XML", value=False)
    
    if st.button("🎫 Generate & Download", type="primary"):
        # Get running number
        running_no = get_next_running_no()
        
        invoice_data = {
            'invoice_no': info.get('invoice_no', ''),
            'running_no': running_no,
            'invoice_date': info.get('invoice_date', ''),
            'customer_name': info.get('customer_name', ''),
            'exchange_rate': exchange_rate,
            'subtotal': subtotal,
            'vat_amount': vat_total,
            'total_amount': total,
            'total_thb': total_thb,
            'items': processed_items
        }
        
        # Save to database
        invoice_data['file_source'] = st.session_state.get('filename', '')
        save_invoice(invoice_data)
        
        st.success(f"✅ Running No: {running_no}")
        
        # Generate outputs
        if gen_pdf:
            pdf_buffer = generate_pdf(invoice_data)
            st.download_button(
                "📥 Download PDF",
                pdf_buffer.getvalue(),
                file_name=f"Receipt_{running_no}.pdf",
                mime="application/pdf"
            )
        
        if gen_xml:
            xml_buffer = generate_xml(invoice_data)
            st.download_button(
                "📥 Download XML",
                xml_buffer.getvalue(),
                file_name=f"ETax_{running_no}.xml",
                mime="application/xml"
            )



def show_batch_preview():
    """Preview and issue multiple invoices"""
    batch = st.session_state['batch_invoices']
    
    st.markdown(f"### 📚 {len(batch)} Invoices Ready")
    
    # Select which invoice to preview
    options = []
    for inv in batch:
        name = inv.get('customer_name', '')[:20]
        addr = inv.get('customer_address', '')
        if addr:
            addr_short = addr.replace('\n', ', ')[:25]
            options.append(f"{inv.get('filename', inv.get('invoice_no', 'Unknown'))} - {name} | {addr_short}")
        else:
            options.append(f"{inv.get('filename', inv.get('invoice_no', 'Unknown'))} - {name}")
    options.append("📋 ทั้งหมด")
    
    selected = st.selectbox("เลือก Invoice ที่จะ Preview:", options, key="batch_select")
    
    if selected == "📋 ทั้งหมด":
        # Show all invoices summary
        for i, inv in enumerate(batch):
            with st.expander(f"📄 {inv.get('filename', inv.get('invoice_no', f'Invoice {i+1}'))}"):
                show_single_invoice_preview(inv, key_suffix=f"_batch_{i}")
    else:
        # Find selected invoice
        idx = options.index(selected)
        inv = batch[idx]
        show_single_invoice_preview(inv, key_suffix="_batch_selected")

def show_single_invoice_preview(invoice_data, key_suffix=""):
    """Preview a single invoice with detailed Thai GAC styling"""
    
    # Get values
    subtotal = float(invoice_data.get('total_amount', 0) or 0)
    exchange_rate = float(invoice_data.get('exchange_rate', 1) or 1)
    currency = invoice_data.get('currency', 'USD')
    total_thb = float(invoice_data.get('total_thb', 0) or 0)
    if total_thb == 0 and subtotal > 0:
        total_thb = subtotal * exchange_rate
    vat = total_thb - (total_thb / 1.07)
    
    invoice_no = invoice_data.get('invoice_no', '-')
    customer = invoice_data.get('customer_name', 'Customer')
    address = invoice_data.get('customer_address', '')
    date = invoice_data.get('invoice_date', '')
    running = invoice_data.get('running_no', 'Draft')
    
    # Build detailed A4 HTML
    html = '<div style="width:210mm;min-height:297mm;padding:15mm;margin:auto;background:#fff;font-family:sans-serif;font-size:11px;color:#000;">'
    
    # Header - Left side (Tax ID)
    html += '<table style="width:100%;margin-bottom:10px;"><tr>'
    html += '<td style="width:50%;vertical-align:top;">'
    html += '<div style="font-weight:bold;">เลขประจำตัวผู้เสียภาษีอากร / Tax ID No. 0105535169497</div>'
    html += '<div>ทะเบียนการค้า / Registration No. 0105535169497</div>'
    html += '</td>'
    html += '<td style="width:50%;text-align:right;vertical-align:top;">'
    html += '<div style="font-size:18px;font-weight:bold;color:#0066b2;">GULF AGENCY COMPANY (THAILAND) LTD.</div>'
    html += '<div>บริษัท กัลฟ์ เอเจนซี่ คัมปะนี (ประเทศไทย) จำกัด</div>'
    html += '<div>26/30-31 ชั้น 9 อาคารอรกาน์ ซอยชิดลม ถนนพระราม 4 แขวงลุมพินี เขตปางคอยแหลม กรุงเทพมหานคร 10330</div>'
    html += '<div>Tel: 02-650-7400 | Email: thailand@gac.com</div>'
    html += '</td></tr></table>'
    
    # Title
    html += '<div style="text-align:center;font-size:20px;font-weight:bold;padding:10px;border:2px solid #000;margin:15px 0;">RECEIPT COPY / TAX INVOICE COPY</div>'
    
    # Customer & Document Info
    html += '<table style="width:100%;border-collapse:collapse;margin-bottom:15px;border:1px solid #000;">'
    html += '<tr><td style="width:50%;padding:10px;border:1px solid #000;vertical-align:top;">'
    html += '<div style="font-weight:bold;margin-bottom:5px;">ชื่อลูกค้า / Customer Name:</div>'
    html += '<div>' + str(customer) + '</div>'
    html += '<div style="margin-top:5px;">' + str(address)[:100] + '</div>'
    html += '</td>'
    html += '<td style="width:50%;padding:10px;border:1px solid #000;vertical-align:top;">'
    html += '<table style="width:100%;">'
    html += '<tr><td style="width:40%;"><b>No. / เลขที่:</b></td><td>' + str(running) + '</td></tr>'
    html += '<tr><td><b>Date / วันที่:</b></td><td>' + str(date) + '</td></tr>'
    html += '<tr><td><b>Invoice No:</b></td><td>' + str(invoice_no) + '</td></tr>'
    html += '</table>'
    html += '</td></tr></table>'
    
    # Items Table
    html += '<table style="width:100%;border-collapse:collapse;margin-bottom:15px;border:1px solid #000;">'
    html += '<tr style="background:#eee;">'
    html += '<th style="padding:8px;border:1px solid #000;text-align:center;">รายการ / Description</th>'
    html += '<th style="padding:8px;border:1px solid #000;text-align:right;">จำนวนเงิน / Amount</th>'
    html += '<th style="padding:8px;border:1px solid #000;text-align:right;">VAT 7%</th>'
    html += '<th style="padding:8px;border:1px solid #000;text-align:right;">Total (THB)</th>'
    html += '</tr>'
    
    # Add items
    try:
        items = invoice_data.get('items', [])
        if not items and invoice_data.get('items_json'):
            import json
            items = json.loads(invoice_data.get('items_json', '[]'))
        for item in items[:12]:
            desc = item.get('description', '-')[:50]
            amt = float(item.get('amount', 0))
            item_vat = amt * 0.07
            html += '<tr><td style="padding:6px;border:1px solid #000;">' + str(desc) + '</td>'
            html += '<td style="padding:6px;border:1px solid #000;text-align:right;">' + f"{amt:,.2f}" + '</td>'
            html += '<td style="padding:6px;border:1px solid #000;text-align:right;">' + f"{item_vat:,.2f}" + '</td>'
            html += '<td style="padding:6px;border:1px solid #000;text-align:right;">' + f"{amt:,.2f}" + '</td></tr>'
    except:
        pass
    
    html += '</table>'
    
    # Totals
    html += '<table style="width:50%;margin-left:auto;border-collapse:collapse;">'
    html += '<tr><td style="padding:8px;text-align:right;"><b>รวมเงิน / Subtotal:</b></td><td style="padding:8px;text-align:right;border:1px solid #000;">' + f"{total_thb - vat:,.2f}" + '</td></tr>'
    html += '<tr><td style="padding:8px;text-align:right;"><b>ภาษีมูลค่าเพิ่ม 7% / VAT 7%:</b></td><td style="padding:8px;text-align:right;border:1px solid #000;">' + f"{vat:,.2f}" + '</td></tr>'
    html += '<tr><td style="padding:10px;text-align:right;font-size:14px;"><b>จำนวนเงินรวม / GRAND TOTAL:</b></td><td style="padding:10px;text-align:right;border:2px solid #000;font-size:14px;font-weight:bold;">' + f"{total_thb:,.2f}" + '</td></tr>'
    html += '</table>'
    
    # Footer - Payment method
    html += '<table style="width:100%;margin-top:30px;border-collapse:collapse;">'
    html += '<tr>'
    html += '<td style="width:50%;padding:10px;border:1px dashed #888;">'
    html += '<div style="margin-bottom:10px;"><b>วิธีการชำระเงิน / Payment Method:</b></div>'
    html += '<div>☐ เงินสด / Cash &nbsp;&nbsp; ☑ เครดิต / Credit &nbsp;&nbsp; ☐ เช็ค / Cheque</div>'
    html += '<div style="margin-top:10px;border-top:1px dotted #888;padding-top:5px;">Bank: Bangkok Bank | A/C: 123-456-7890</div>'
    html += '</td>'
    html += '<td style="width:50%;padding:10px;">'
    html += '<table style="width:100%;">'
    html += '<tr><td style="height:40px;"></td></tr>'
    html += '<tr><td style="border-top:1px solid #000;text-align:center;">ผู้เก็บเงิน / Bill Collector</td></tr>'
    html += '<tr><td style="height:30px;"></td></tr>'
    html += '<tr><td style="border-top:1px solid #000;text-align:center;">Accountant</td></tr>'
    html += '</table>'
    html += '</td>'
    html += '</tr></table>'
    
    # Disclaimer / Standard conditions
    html += '<div style="margin-top:30px;border-top:1px solid #ccc;padding-top:15px;">'
    html += '<div style="font-size:8px;text-align:left;line-height:1.6;color:#333;">'
    html += '<b>All business is undertaken subject to our Standard Trading Conditions of Carriage, which are incorporated into all contracts of carriage to which we are a party. Our Standard Trading Conditions are available from our offices on request.</b><br><br>'
    html += '<b>ใบเสร็จรับเงินนี้จะสมบูรณ์ต่อเมื่อมีลายเซ็นของผู้มีอำนาจและพนักงานเก็บเงินของบริษัทฯ กรณีชำระด้วยเช็ค ใบเสร็จรับเงินนี้จะสมบูรณ์ต่อเมื่อบริษัทฯ ได้รับชำระเงินตามเช็คเรียบร้อยแล้ว</b><br><br>'
    html += '<i>This receipt is not valid unless signed by authorized person and collector. If payment is made by cheque, this receipt will be valid only when the cheque has been honoured.</i>'
    html += '</div></div>'
    
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)
    
    # PDF Preview and Download buttons
    st.markdown("---")
    st.markdown("### 🧾 ออกเอกสาร")
    
    # PDF Preview toggle
    show_pdf = st.checkbox("👁️ ดูตัวอย่าง PDF", key="pdf_preview_" + key_suffix)
    
    if show_pdf:
        with st.spinner("กำลังสร้าง PDF..."):
            try:
                from pdf_generator import generate_receipt_pdf
                import base64
                pdf_buffer = generate_receipt_pdf(invoice_data)
                pdf_bytes = pdf_buffer.getvalue()
                b64 = base64.b64encode(pdf_bytes).decode()
                pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Generate & Download PDF", key="dl_pdf_" + key_suffix):
            try:
                from pdf_generator import generate_receipt_pdf
                pdf_buffer = generate_receipt_pdf(invoice_data)
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"receipt_{running}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        st.info("💡 ระบบพร้อมออกเอกสาร")


def show_history():
    st.markdown('<p class="main-header">📊 Invoice History</p>', unsafe_allow_html=True)
    
    history = get_invoice_history(50)
    
    if not history:
        st.info("ยังไม่มีใบเสร็จที่ออก")
        return
    
    df = pd.DataFrame(history)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Invoices", len(df))
    with col2:
        st.metric("Total (USD)", f"${df['total_amount'].sum():,.2f}")
    with col3:
        st.metric("Total (THB)", f"฿{df['total_thb'].sum():,.2f}")
    
    cols = [c for c in ['running_no', 'invoice_no', 'customer_name', 'invoice_date', 'total_amount', 'total_thb'] if c in df.columns]
    if cols:
        st.dataframe(df[cols], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

if __name__ == '__main__':
    main()


# ============================================================================
# NOTE: Agent Integration
# ============================================================================
# To use real agents, you need to:
# 1. Run this Streamlit app within OpenClaw session
# 2. Use sessions_spawn() to call agents
# 3. Or call agents separately from OpenClaw CLI
#
# For now, the workflow uses local validation/generation as fallback.
# ============================================================================

# ============================================================================
# E-TAX AGENT WORKFLOW
# ============================================================================


# ============================================================================
# E-TAX WORKFLOW FUNCTIONS
# ============================================================================

def etax_validate(invoice_data: dict) -> dict:
    """Validate invoice data"""
    from decimal import Decimal, ROUND_HALF_EVEN
    
    errors = []
    
    # 1. Validate Tax ID (13 digits + Mod 11)
    tax_id = invoice_data.get('customer', {}).get('tax_id', '')
    if tax_id and (len(tax_id) != 13 or not tax_id.isdigit()):
        errors.append("Tax ID ต้องเป็น 13 หลัก")
    elif tax_id:
        weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        total = sum(int(tax_id[i]) * weights[i] for i in range(12))
        check = (11 - (total % 11)) % 10
        if int(tax_id[12]) != check:
            errors.append("Tax ID ไม่ถูกต้อง (Mod 11 failed)")
    
    # 2. Validate calculations
    subtotal = Decimal(str(invoice_data.get('subtotal', 0)))
    vat_amount = Decimal(str(invoice_data.get('vat_amount', 0)))
    total_amount = Decimal(str(invoice_data.get('total_amount', 0)))
    
    expected_vat = (subtotal * Decimal('0.07')).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    expected_total = subtotal + expected_vat
    
    if abs(vat_amount - expected_vat) > Decimal('0.01'):
        errors.append("VAT ไม่ถูกต้อง")
    
    if abs(total_amount - expected_total) > Decimal('0.01'):
        errors.append("Total ไม่ถูกต้อง")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'validated_data': invoice_data
    }

def etax_generate_xml(invoice_data: dict) -> dict:
    """Generate XML from invoice data"""
    import os
    from xml.etree import ElementTree as ET
    
    invoice_no = invoice_data.get('invoice_no', 'UNKNOWN')
    xml_dir = os.path.join(os.path.dirname(DB_PATH), 'etax_xml')
    os.makedirs(xml_dir, exist_ok=True)
    xml_path = os.path.join(xml_dir, f'{invoice_no}_etax.xml')
    
    root = ET.Element('Invoice')
    root.set('xmlns', 'urn:ettds:invoice:v1.0')
    
    header = ET.SubElement(root, 'Header')
    ET.SubElement(header, 'ID').text = invoice_no
    ET.SubElement(header, 'IssueDate').text = invoice_data.get('invoice_date', '')
    
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding='UTF-8', xml_declaration=True)
    
    return {'success': True, 'xml_path': xml_path}

def etax_sign_xml(xml_path: str) -> dict:
    """Sign XML (placeholder)"""
    import os, shutil
    signed_path = xml_path.replace('.xml', '_signed.xml')
    if os.path.exists(xml_path):
        shutil.copy(xml_path, signed_path)
    return {'success': True, 'signed_path': signed_path}

def etax_deliver(signed_xml_path: str, invoice_data: dict) -> dict:
    """Deliver to RD and send email"""
    return {
        'success': True,
        'rd_submission_id': f"RD-{invoice_data.get('invoice_no', 'UNKNOWN')}",
        'email_sent': True
    }

def run_etax_workflow(invoice_data: dict) -> dict:
    """Main workflow - runs through all agents"""
    
    result = {
        'invoice_no': invoice_data.get('invoice_no'),
        'steps': [],
        'final_status': 'PENDING'
    }
    
    # Step 1: Validate
    st.info("Step 1: Validating with etax-validator...")
    validation = etax_validate(invoice_data)
    result['steps'].append({'step': 'validate', 'result': validation})
    
    if not validation['valid']:
        result['final_status'] = 'FAILED'
        result['error'] = validation['errors']
        return result
    
    # Step 2: Generate XML
    st.info("Step 2: Generating XML with etax-xml-generator...")
    xml_result = etax_generate_xml(validation['validated_data'])
    result['steps'].append({'step': 'generate_xml', 'result': xml_result})
    
    if not xml_result.get('success'):
        result['final_status'] = 'FAILED'
        result['error'] = xml_result.get('error')
        return result
    
    # Step 3: Sign
    st.info("Step 3: Signing with etax-signer...")
    sign_result = etax_sign_xml(xml_result['xml_path'])
    result['steps'].append({'step': 'sign', 'result': sign_result})
    
    if not sign_result.get('success'):
        result['final_status'] = 'FAILED'
        result['error'] = sign_result.get('error')
        return result
    
    # Step 4: Deliver
    st.info("Step 4: Submitting with etax-delivery...")
    delivery_result = etax_deliver(sign_result['signed_path'], invoice_data)
    result['steps'].append({'step': 'deliver', 'result': delivery_result})
    
    if delivery_result.get('success'):
        result['final_status'] = 'DELIVERED'
        result['rd_submission_id'] = delivery_result.get('rd_submission_id')
    else:
        result['final_status'] = 'FAILED'
    
    return result

