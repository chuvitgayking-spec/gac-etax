"""
E-Tax XML Generator
Generates CII XML (ขมธ. 3-2560) compliant invoices
"""
import os
import json
import logging
from typing import Dict, Optional, List
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import datetime
from xml.etree import ElementTree as ET

from config import Config
from utils.error_handling import XMLValidationError, validate_required_fields

logger = logging.getLogger('etax')


class XMLGenerator:
    """
    Generate CII XML for Thai e-Tax Invoice (ขมธ. 3-2560)
    
    Namespace references:
    - rsm: urn:un:unece:uncefact:data:standard:InvoiceType
    - ram: urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntityType
    - udt: urn:un:unece:uncefact:data:standard:UnqualifiedDataType
    """
    
    # CII Namespaces
    NS = {
        'xmlns': 'urn:un:unece:uncefact:data:standard:InvoiceType',
        'xmlns:rsm': 'urn:un:unece:uncefact:data:standard:InvoiceType',
        'xmlns:ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntityType',
        'xmlns:udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.logger = logger
    
    def generate(self, invoice_data: dict, output_path: str = None) -> dict:
        """
        Generate CII XML from invoice data
        
        Args:
            invoice_data: Invoice information dictionary
            output_path: Optional path to save XML file
        
        Returns:
            Dictionary with success status and XML path/string
        """
        try:
            # Validate required fields
            validate_required_fields(invoice_data, [
                'invoice_no', 'invoice_date', 'customer_name', 
                'items', 'subtotal', 'vat_amount', 'total_amount'
            ], context='invoice_data')
            
            # Create XML root
            root = self._create_root()
            
            # Add document context
            self._add_context(root)
            
            # Add document header
            self._add_header(root, invoice_data)
            
            # Add supply chain trade transaction
            self._add_transaction(root, invoice_data)
            
            # Convert to string
            xml_string = ET.tostring(
                root, 
                encoding='UTF-8', 
                xml_declaration=True
            ).decode('utf-8')
            
            # Save to file if path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(xml_string)
                self.logger.info(f"XML saved to {output_path}")
            
            return {
                'success': True,
                'xml': xml_string,
                'output_path': output_path,
                'invoice_no': invoice_data.get('invoice_no')
            }
            
        except Exception as e:
            self.logger.error(f"XML generation failed: {e}")
            raise XMLValidationError(
                message=str(e),
                details={'invoice_no': invoice_data.get('invoice_no')}
            )
    
    def _create_root(self) -> ET.Element:
        """Create root element with namespaces"""
        root = ET.Element('Invoice')
        for prefix, uri in self.NS.items():
            root.set(prefix, uri)
        return root
    
    def _add_context(self, root: ET.Element) -> None:
        """Add document context (ExchangedDocumentContext)"""
        context = ET.SubElement(root, 'rsm:ExchangedDocumentContext')
        
        # Business process
        bp = ET.SubElement(context, 'ram:BusinessProcessSpecifiedDocumentContextParameter')
        ET.SubElement(bp, 'ram:ID').text = 'FC'  # Full Tax Invoice
        
        # Guideline
        guideline = ET.SubElement(context, 'ram:GuidelineSpecifiedDocumentContextParameter')
        ET.SubElement(guideline, 'ram:ID').text = 'urn:thai-tax:inv:v1.0'
    
    def _add_header(self, root: ET.Element, data: dict) -> None:
        """Add document header (ExchangedDocument)"""
        header = ET.SubElement(root, 'rsm:ExchangedDocument')
        
        # Invoice number
        ET.SubElement(header, 'ram:ID').text = data.get('invoice_no', '')
        
        # Issue date
        issue_date = data.get('invoice_date', '')
        if isinstance(issue_date, str):
            # Try to parse and format
            try:
                dt = datetime.strptime(issue_date, '%d %b %Y')
                issue_date = dt.strftime('%Y-%m-%d')
            except:
                pass
        ET.SubElement(header, 'ram:IssueDateTime').text = str(issue_date)
        
        # Document type: 380 = Tax Invoice
        ET.SubElement(header, 'ram:DocumentTypeCode').text = '380'
    
    def _add_transaction(self, root: ET.Element, data: dict) -> None:
        """Add supply chain trade transaction (body)"""
        transaction = ET.SubElement(root, 'rsm:SupplyChainTradeTransaction')
        
        # Header agreement (Seller/Buyer)
        self._add_header_agreement(transaction, data)
        
        # Line items
        self._add_line_items(transaction, data)
        
        # Settlement (totals)
        self._add_settlement(transaction, data)
    
    def _add_header_agreement(self, transaction: ET.Element, data: dict) -> None:
        """Add header trade agreement (seller and buyer)"""
        agreement = ET.SubElement(
            transaction, 
            'ram:ApplicableHeaderTradeAgreement'
        )
        
        # Seller
        seller = ET.SubElement(agreement, 'ram:SellerTradeParty')
        ET.SubElement(seller, 'ram:ID', {
            'schemeID': 'TH'
        }).text = self.config.COMPANY_TAX_ID
        ET.SubElement(seller, 'ram:Name').text = self.config.COMPANY_NAME
        
        # Seller address
        seller_addr = ET.SubElement(seller, 'ram:PostalTradeAddress')
        addr = self.config.COMPANY_ADDRESS
        ET.SubElement(seller_addr, 'ram:StreetName').text = addr[:200] if addr else ''
        ET.SubElement(seller_addr, 'ram:CityName').text = 'BANGKOK'
        ET.SubElement(seller_addr, 'ram:CountryID').text = 'TH'
        
        # Seller tax registration
        tax_reg = ET.SubElement(seller, 'ram:SpecifiedTaxRegistration')
        ET.SubElement(tax_reg, 'ram:ID').text = self.config.COMPANY_TAX_ID
        
        # Buyer
        buyer = ET.SubElement(agreement, 'ram:BuyerTradeParty')
        cust = data.get('customer', {})
        
        # Buyer tax ID (if available)
        if cust.get('tax_id'):
            ET.SubElement(buyer, 'ram:ID', {
                'schemeID': 'TH'
            }).text = cust.get('tax_id')
        
        ET.SubElement(buyer, 'ram:Name').text = cust.get('name', data.get('customer_name', ''))
        
        # Buyer address
        buyer_addr = ET.SubElement(buyer, 'ram:PostalTradeAddress')
        buyer_addr_text = cust.get('address', data.get('customer_address', ''))
        ET.SubElement(buyer_addr, 'ram:StreetName').text = buyer_addr_text[:200] if buyer_addr_text else ''
        ET.SubElement(buyer_addr, 'ram:CountryID').text = 'TH'
    
    def _add_line_items(self, transaction: ET.Element, data: dict) -> None:
        """Add line items"""
        items = data.get('items', [])
        
        for i, item in enumerate(items, 1):
            line_item = ET.SubElement(
                transaction, 
                'ram:IncludedSupplyChainTradeLineItem'
            )
            
            # Trade product
            product = ET.SubElement(line_item, 'ram:SpecifiedTradeProduct')
            ET.SubElement(product, 'ram:Name').text = item.get('description', '')
            
            # Quantity
            quantity = ET.SubElement(line_item, 'ram:SpecifiedLineTradeAgreement')
            ET.SubElement(quantity, 'ram:Quantity', {
                'unitCode': item.get('unit', 'EA')
            }).text = str(item.get('quantity', 1))
            
            # Unit price
            unit_price = ET.SubElement(quantity, 'ram:UnitPrice')
            ET.SubElement(unit_price, 'ram:Amount', {
                'currencyID': 'THB'
            }).text = self._format_decimal(item.get('unit_price', 0))
            
            # Line total
            line_total = ET.SubElement(line_item, 'ram:SpecifiedLineTradeSettlement')
            ET.SubElement(line_total, 'ram:LineTotalAmount', {
                'currencyID': 'THB'
            }).text = self._format_decimal(item.get('amount', 0))
    
    def _add_settlement(self, transaction: ET.Element, data: dict) -> None:
        """Add settlement (totals)"""
        settlement = ET.SubElement(
            transaction, 
            'ram:ApplicableHeaderTradeSettlement'
        )
        
        # Payment means
        ET.SubElement(settlement, 'ram:PaymentMeansCode').text = '42'
        
        # Tax currency
        ET.SubElement(settlement, 'ram:TaxCurrencyCode').text = 'THB'
        
        # Grand total (excluding VAT)
        ET.SubElement(settlement, 'ram:TaxTotalAmount', {
            'currencyID': 'THB'
        }).text = self._format_decimal(data.get('subtotal', 0))
        
        # VAT amount
        ET.SubElement(settlement, 'ram:TaxTotalAmount', {
            'currencyID': 'THB'
        }).text = self._format_decimal(data.get('vat_amount', 0))
        
        # Grand total (including VAT)
        ET.SubElement(settlement, 'ram:GrandTotalAmount', {
            'currencyID': 'THB'
        }).text = self._format_decimal(data.get('total_amount', 0))
        
        # Net payable
        ET.SubElement(settlement, 'ram:NetPayableAmount', {
            'currencyID': 'THB'
        }).text = self._format_decimal(data.get('total_amount', 0))
    
    @staticmethod
    def _format_decimal(value) -> str:
        """Format decimal value for XML"""
        if value is None:
            return '0.00'
        
        try:
            decimal_val = Decimal(str(value))
            return str(decimal_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN))
        except:
            return '0.00'
    
    def validate_xml(self, xml_string: str) -> dict:
        """
        Validate XML structure
        
        Returns:
            Validation result dictionary
        """
        try:
            root = ET.fromstring(xml_string)
            
            # Check root element
            if root.tag != 'Invoice':
                return {'valid': False, 'error': 'Root must be Invoice'}
            
            # Check required elements exist
            required = [
                'rsm:ExchangedDocumentContext',
                'rsm:ExchangedDocument',
                'rsm:SupplyChainTradeTransaction'
            ]
            
            missing = []
            for tag in required:
                if root.find(f'.//{tag}') is None:
                    missing.append(tag)
            
            return {
                'valid': len(missing) == 0,
                'missing_elements': missing
            }
            
        except ET.ParseError as e:
            return {'valid': False, 'error': f'XML parse error: {e}'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}


# Convenience function
def generate_etax_xml(invoice_data: dict, output_path: str = None) -> dict:
    """Generate e-Tax XML"""
    generator = XMLGenerator()
    return generator.generate(invoice_data, output_path)
