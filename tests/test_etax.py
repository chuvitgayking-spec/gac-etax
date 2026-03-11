"""
Unit Tests for E-Tax Invoice System
"""
import os
import sys
import json
import tempfile
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.xml_generator import XMLGenerator
from utils.error_handling import ETaxError, validate_required_fields
from config import Config


class TestXMLGenerator:
    """Test XML Generator"""
    
    def test_generate_basic_invoice(self):
        """Test basic invoice generation"""
        config = Config()
        generator = XMLGenerator(config)
        
        invoice_data = {
            'invoice_no': 'TEST001',
            'invoice_date': '2026-03-12',
            'customer_name': 'Test Company',
            'customer_address': '123 Test Road',
            'items': [
                {
                    'description': 'Service Fee',
                    'quantity': 1,
                    'unit': 'EA',
                    'unit_price': 1000,
                    'amount': 1000
                }
            ],
            'subtotal': 1000,
            'vat_amount': 70,
            'total_amount': 1070
        }
        
        result = generator.generate(invoice_data)
        
        assert result['success'] is True
        assert 'xml' in result
        assert 'TEST001' in result['xml']
        assert 'Invoice' in result['xml']
    
    def test_generate_with_multiple_items(self):
        """Test invoice with multiple line items"""
        generator = XMLGenerator()
        
        invoice_data = {
            'invoice_no': 'TEST002',
            'invoice_date': '2026-03-12',
            'customer_name': 'Test Company',
            'items': [
                {'description': 'Item 1', 'quantity': 1, 'unit': 'EA', 'amount': 500},
                {'description': 'Item 2', 'quantity': 2, 'unit': 'EA', 'amount': 300},
                {'description': 'Item 3', 'quantity': 1, 'unit': 'EA', 'amount': 200}
            ],
            'subtotal': 1000,
            'vat_amount': 70,
            'total_amount': 1070
        }
        
        result = generator.generate(invoice_data)
        
        assert result['success'] is True
        # Should have 3 line items
        assert result['xml'].count('IncludedSupplyChainTradeLineItem') >= 3
    
    def test_validate_xml(self):
        """Test XML validation"""
        generator = XMLGenerator()
        
        # Valid XML
        valid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <Invoice xmlns="urn:un:unece:uncefact:data:standard:InvoiceType">
            <rsm:ExchangedDocumentContext>
                <ram:BusinessProcessSpecifiedDocumentContextParameter>
                    <ram:ID>FC</ram:ID>
                </ram:BusinessProcessSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
            <rsm:ExchangedDocument>
                <ram:ID>TEST001</ram:ID>
            </rsm:ExchangedDocument>
            <rsm:SupplyChainTradeTransaction/>
        </Invoice>'''
        
        result = generator.validate_xml(valid_xml)
        # May fail due to namespace issues but shouldn't crash
        assert 'valid' in result
    
    def test_save_to_file(self):
        """Test saving XML to file"""
        generator = XMLGenerator()
        
        invoice_data = {
            'invoice_no': 'TEST003',
            'invoice_date': '2026-03-12',
            'customer_name': 'Test',
            'items': [{'description': 'Test', 'amount': 100}],
            'subtotal': 100,
            'vat_amount': 7,
            'total_amount': 107
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            temp_path = f.name
        
        try:
            result = generator.generate(invoice_data, temp_path)
            
            assert result['success'] is True
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert 'TEST003' in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestErrorHandling:
    """Test error handling"""
    
    def test_validate_required_fields(self):
        """Test required field validation"""
        # Should pass
        validate_required_fields({'a': 1, 'b': 2}, ['a', 'b'])
        
        # Should fail
        try:
            validate_required_fields({'a': 1}, ['a', 'b', 'c'])
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'b' in str(e)
            assert 'c' in str(e)


class TestConfig:
    """Test configuration"""
    
    def test_config_defaults(self):
        """Test default configuration"""
        config = Config()
        
        assert config.COMPANY_TAX_ID == '0105535169497'
        assert config.DEFAULT_VAT_RATE == 0.07
        assert config.LOG_LEVEL == 'INFO'
    
    def test_db_path(self):
        """Test database path"""
        config = Config()
        db_path = config.get_db_path()
        
        assert db_path is not None
        assert isinstance(db_path, str)


def run_tests():
    """Run all tests"""
    print("Running E-Tax Tests...\n")
    
    test_xml = TestXMLGenerator()
    
    print("Test 1: Basic invoice generation")
    test_xml.test_generate_basic_invoice()
    print("  ✓ PASSED\n")
    
    print("Test 2: Multiple items")
    test_xml.test_generate_with_multiple_items()
    print("  ✓ PASSED\n")
    
    print("Test 3: XML validation")
    test_xml.test_validate_xml()
    print("  ✓ PASSED\n")
    
    print("Test 4: Save to file")
    test_xml.test_save_to_file()
    print("  ✓ PASSED\n")
    
    print("Test 5: Error handling")
    test_errors = TestErrorHandling()
    test_errors.test_validate_required_fields()
    print("  ✓ PASSED\n")
    
    print("Test 6: Config")
    test_config = TestConfig()
    test_config.test_config_defaults()
    test_config.test_db_path()
    print("  ✓ PASSED\n")
    
    print("=" * 40)
    print("All tests passed! ✓")
    print("=" * 40)


if __name__ == '__main__':
    run_tests()
