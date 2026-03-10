"""
Tax Mapping Module for e-Tax Invoice System
Manages flexible tax categorization rules
"""

import csv
import os
from decimal import Decimal

MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'data', 'tax_mapping.csv')

# Default mapping if file doesn't exist
DEFAULT_MAPPING = {
    'NON_VAT': [
        'TRANSPORTATION',
        'AIR FREIGHT', 
        'OCEAN FREIGHT',
        'CUSTOMS FEE',
        'PROFIT SHARE',
        'EXPORT',
        'FUEL',
        'AWB',
        'FWB',
        'TERMINAL'
    ],
    'PARTIAL_VAT': [
        'OCEAN FREIGHT'  # Special case - user defines amount
    ],
    'VAT_7': [
        'CUSTOMS CLEARANCE',
        'HANDLING',
        'LABOUR',
        'ADDITIONAL',
        'LOCAL'
    ]
}

def load_mapping():
    """Load tax mapping from CSV file"""
    mapping = {'NON_VAT': [], 'PARTIAL_VAT': [], 'VAT_7': []}
    
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    keyword = row.get('keyword', '').strip().upper()
                    category = row.get('category', '').strip().upper()
                    if keyword and category in mapping:
                        mapping[category].append(keyword)
        except Exception as e:
            print(f"Error loading mapping: {e}")
    
    # If no mapping file, use defaults
    if not any(mapping.values()):
        mapping = DEFAULT_MAPPING.copy()
        save_mapping(mapping)
    
    return mapping

def save_mapping(mapping):
    """Save tax mapping to CSV file"""
    os.makedirs(os.path.dirname(MAPPING_FILE), exist_ok=True)
    
    with open(MAPPING_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['keyword', 'category', 'description'])
        
        for category, keywords in mapping.items():
            for keyword in keywords:
                desc = get_category_description(category)
                writer.writerow([keyword, category, desc])

def get_category_description(category):
    """Get description for category"""
    descriptions = {
        'NON_VAT': 'บริการระหว่างประเทศ/ยกเว้นภาษี',
        'PARTIAL_VAT': 'บางส่วน-ต้องกรอกจำนวน',
        'VAT_7': 'บริการในประเทศ 7%'
    }
    return descriptions.get(category, '')

def determine_category(description, mapping):
    """Determine tax category based on description"""
    desc_upper = description.upper()
    
    # Check PARTIAL_VAT first (special case)
    for keyword in mapping.get('PARTIAL_VAT', []):
        if keyword in desc_upper:
            return 'PARTIAL_VAT'
    
    # Check NON_VAT
    for keyword in mapping.get('NON_VAT', []):
        if keyword in desc_upper:
            return 'NON_VAT'
    
    # Default to VAT_7
    return 'VAT_7'

def get_vat_rate(category):
    """Get VAT rate for category"""
    rates = {
        'NON_VAT': 0,
        'PARTIAL_VAT': 7,  # Partial - user defines
        'VAT_7': 7
    }
    return rates.get(category, 0)

def add_keyword_to_category(keyword, category, mapping):
    """Add keyword to category"""
    keyword = keyword.upper().strip()
    if keyword and category in mapping:
        if keyword not in mapping[category]:
            mapping[category].append(keyword)
            save_mapping(mapping)
    return mapping

def remove_keyword_from_category(keyword, category, mapping):
    """Remove keyword from category"""
    keyword = keyword.upper().strip()
    if keyword and category in mapping:
        mapping[category] = [k for k in mapping[category] if k != keyword]
        save_mapping(mapping)
    return mapping

# Load on import
TAX_MAPPING = load_mapping()
