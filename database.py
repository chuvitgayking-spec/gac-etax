"""
Database Module for e-Tax Invoice System
Manages running numbers and invoice history using SQLite
"""

import sqlite3
import os
from datetime import datetime
from decimal import Decimal

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'etax.db')

def get_db_connection():
    """Get database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Running number table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS running_numbers (
            id INTEGER PRIMARY KEY,
            prefix TEXT NOT NULL,
            last_number INTEGER NOT NULL DEFAULT 0,
            year INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Invoice history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            running_no TEXT NOT NULL,
            customer_name TEXT,
            customer_tax_id TEXT,
            invoice_date TEXT,
            subtotal DECIMAL(12,2),
            vat_amount DECIMAL(12,2),
            total_amount DECIMAL(12,2),
            total_thb DECIMAL(12,2),
            exchange_rate DECIMAL(12,6),
            file_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Invoice items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            item_no INTEGER,
            description TEXT,
            amount DECIMAL(12,2),
            vat_rate INTEGER,
            vat_amount DECIMAL(12,2),
            amount_thb DECIMAL(12,2),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_next_running_number(prefix='GAC', year=None):
    """Get next running number"""
    if year is None:
        year = datetime.now().year
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute('''
        SELECT last_number FROM running_numbers 
        WHERE prefix = ? AND year = ?
    ''', (prefix, year))
    
    row = cursor.fetchone()
    
    if row:
        new_number = row[0] + 1
        cursor.execute('''
            UPDATE running_numbers 
            SET last_number = ?, updated_at = CURRENT_TIMESTAMP
            WHERE prefix = ? AND year = ?
        ''', (new_number, prefix, year))
    else:
        new_number = 1
        cursor.execute('''
            INSERT INTO running_numbers (prefix, last_number, year)
            VALUES (?, ?, ?)
        ''', (prefix, 1, year))
    
    conn.commit()
    conn.close()
    
    # Format: 2026-0001
    return f"{year}-{new_number:04d}"

def save_invoice(invoice_data):
    """Save invoice to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert invoice header
    cursor.execute('''
        INSERT INTO invoices (
            invoice_no, running_no, customer_name, customer_tax_id,
            invoice_date, subtotal, vat_amount, total_amount,
            total_thb, exchange_rate, file_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        invoice_data['invoice_no'],
        invoice_data['running_no'],
        invoice_data['customer_name'],
        invoice_data.get('customer_tax_id', ''),
        invoice_data['invoice_date'],
        float(invoice_data['subtotal']),
        float(invoice_data['vat_amount']),
        float(invoice_data['total_amount']),
        float(invoice_data['total_thb']),
        float(invoice_data['exchange_rate']),
        invoice_data.get('file_source', '')
    ))
    
    invoice_id = cursor.lastrowid
    
    # Insert items
    for item in invoice_data['items']:
        cursor.execute('''
            INSERT INTO invoice_items (
                invoice_id, item_no, description, amount,
                vat_rate, vat_amount, amount_thb
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_id,
            item['item_no'],
            item['description'],
            float(item['amount']),
            item['vat_rate'],
            float(item['vat_amount']),
            float(item['amount_thb'])
        ))
    
    conn.commit()
    conn.close()
    
    return invoice_id

def get_invoice_history(limit=50):
    """Get invoice history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM invoices 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_invoice_by_no(invoice_no):
    """Get specific invoice"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM invoices WHERE invoice_no = ?', (invoice_no,))
    invoice = cursor.fetchone()
    
    if invoice:
        invoice = dict(invoice)
        cursor.execute('SELECT * FROM invoice_items WHERE invoice_id = ?', (invoice['id'],))
        invoice['items'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return invoice

# Initialize on import
init_database()
