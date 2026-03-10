# Invoice Database Functions
INVOICE_DB = '/tmp/invoice_records.db'

def init_invoice_db():
    import sqlite3
    conn = sqlite3.connect(INVOICE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        invoice_no TEXT,
        customer_name TEXT,
        job_number TEXT,
        invoice_date TEXT,
        running_no TEXT,
        exchange_rate REAL,
        subtotal REAL,
        vat_amount REAL,
        total_usd REAL,
        total_thb REAL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def save_invoice_record(invoice_data, running_no):
    import sqlite3
    conn = sqlite3.connect(INVOICE_DB)
    c = conn.cursor()
    total_usd = float(invoice_data.get('total_amount', 0))
    exchange_rate = float(invoice_data.get('exchange_rate', 30.909))
    total_thb = total_usd * exchange_rate
    subtotal = total_usd / 1.07
    vat_amount = total_usd - subtotal
    
    c.execute('''INSERT INTO invoices 
        (filename, invoice_no, customer_name, job_number, invoice_date, running_no, exchange_rate, subtotal, vat_amount, total_usd, total_thb, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued')''',
        (invoice_data.get('filename', ''),
         invoice_data.get('invoice_no', ''),
         invoice_data.get('customer_name', ''),
         invoice_data.get('job_number', ''),
         invoice_data.get('invoice_date', ''),
         running_no,
         exchange_rate,
         subtotal,
         vat_amount,
         total_usd,
         total_thb))
    conn.commit()
    conn.close()

def get_next_running_no():
    import sqlite3
    from datetime import datetime
    year_short = str(datetime.now().year)[-2:]
    conn = sqlite3.connect(INVOICE_DB)
    c = conn.cursor()
    c.execute(f"SELECT running_no FROM invoices WHERE running_no LIKE '{year_short}-%' ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        last_no = row[0]
        seq = int(last_no.split('-')[1]) + 1
    else:
        seq = 1
    return f"{year_short}-{seq:04d}"

def get_issued_invoices():
    import sqlite3
    conn = sqlite3.connect(INVOICE_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM invoices ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows
