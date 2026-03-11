"""
E-Tax Tools Package
"""
from .core import (
    setup_logging,
    calculate_tax_decimal,
    calculate_reverse_tax,
    tool_checksum_taxid,
    validate_branch_code,
    get_etda_code,
    TaxValidator
)

from .xml_generator import XMLGenerator

__all__ = [
    'setup_logging',
    'calculate_tax_decimal',
    'calculate_reverse_tax',
    'tool_checksum_taxid',
    'validate_branch_code',
    'get_etda_code',
    'TaxValidator',
    'XMLGenerator'
]

__version__ = '1.0.0'
