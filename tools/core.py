"""
E-Tax Core Tools
Modular Python package for E-Tax Invoice processing
"""
import os
import json
import logging
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Dict, List, Optional

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging(log_level: str = None, log_file: str = None) -> logging.Logger:
    """Setup JSON logging for production"""
    logger = logging.getLogger('etax')
    logger.setLevel(getattr(logging, log_level or os.getenv('LOG_LEVEL', 'INFO')))
    
    # JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': self.formatTime(record),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
            }
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
            return json.dumps(log_data)
    
    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(JSONFormatter())
    logger.addHandler(console)
    
    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

# ============================================================================
# TAX CALCULATOR TOOLS
# ============================================================================

def calculate_tax_decimal(net_amount: float, vat_rate: float = 0.07) -> dict:
    """Calculate VAT using Decimal for precision"""
    net = Decimal(str(net_amount))
    vat = (net * Decimal(str(vat_rate))).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    total = net + vat
    
    return {
        'net': float(net),
        'vat': float(vat),
        'total': float(total),
        'vat_rate': vat_rate
    }

def calculate_reverse_tax(total_amount: float, vat_rate: float = 0.07) -> dict:
    """Calculate backwards from total (VAT inclusive)"""
    total = Decimal(str(total_amount))
    rate = Decimal('1') + Decimal(str(vat_rate))
    net = (total / rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    vat = total - net
    
    return {
        'net': float(net),
        'vat': float(vat),
        'total': float(total)
    }

# ============================================================================
# TAX ID VALIDATION
# ============================================================================

def tool_checksum_taxid(tax_id: str) -> dict:
    """Validate Thai Tax ID using Modulo 11"""
    tax_id = tax_id.replace('-', '').replace(' ', '')
    
    if len(tax_id) != 13 or not tax_id.isdigit():
        return {'valid': False, 'error': 'Must be 13 digits'}
    
    weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    total = sum(int(tax_id[i]) * weights[i] for i in range(12))
    check = (11 - (total % 11)) % 10
    
    if int(tax_id[12]) != check:
        return {'valid': False, 'error': 'Checksum failed'}
    
    return {'valid': True, 'tax_id': tax_id}

def validate_branch_code(branch_code: str) -> bool:
    """Validate 5-digit branch code"""
    branch = branch_code.replace('-', '').replace(' ', '')
    return len(branch) == 5 and branch.isdigit()

# ============================================================================
# ETDA CODE MAPPING
# ============================================================================

def get_etda_code(category: str, value: str) -> str:
    """Map values to ETDA standard codes"""
    mappings = {
        'unit': {
            'ชิ้น': 'PCE', 'กล่อง': 'BX', 'กิโลกรัม': 'KGM',
            'ตัน': 'TNE', 'ลิตร': 'LTR', 'เมตร': 'MTR', 'คู่': 'PR'
        },
        'province': {
            'กรุงเทพ': 'TH-10', 'กรุงเทพฯ': 'TH-10',
            'ชลบุรี': 'TH-20', 'เชียงใหม่': 'TH-50'
        },
        'country': {
            'ไทย': 'TH', 'Thailand': 'TH', 'สิงคโปร์': 'SG'
        },
        'currency': {
            'THB': 'THB', 'บาท': 'THB', 'USD': 'USD', 'EUR': 'EUR'
        }
    }
    return mappings.get(category, {}).get(value, value)

# ============================================================================
# VALIDATOR
# ============================================================================

class TaxValidator:
    """Main validator class"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or setup_logging()
    
    def validate_invoice(self, invoice_data: dict) -> dict:
        """Validate complete invoice data"""
        errors = []
        warnings = []
        
        # Validate Tax ID
        tax_id = invoice_data.get('customer', {}).get('tax_id', '')
        if tax_id:
            tax_id_result = tool_checksum_taxid(tax_id)
            if not tax_id_result['valid']:
                errors.append(f"Tax ID: {tax_id_result['error']}")
        
        # Validate calculations
        subtotal = Decimal(str(invoice_data.get('subtotal', 0)))
        vat_amount = Decimal(str(invoice_data.get('vat_amount', 0)))
        total_amount = Decimal(str(invoice_data.get('total_amount', 0)))
        
        expected_vat = (subtotal * Decimal('0.07')).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        expected_total = subtotal + expected_vat
        
        if abs(vat_amount - expected_vat) > Decimal('0.01'):
            errors.append("VAT calculation mismatch")
        
        if abs(total_amount - expected_total) > Decimal('0.01'):
            errors.append("Total calculation mismatch")
        
        # Validate mandatory fields
        if not invoice_data.get('customer', {}).get('name'):
            errors.append("Customer name required")
        
        result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validated_data': invoice_data
        }
        
        self.logger.info(f"Validation result: {result['valid']}")
        return result
