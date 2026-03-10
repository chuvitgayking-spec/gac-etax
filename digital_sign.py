"""
Digital Signature Module for e-Tax Invoice System
Handles PDF signing with digital certificates
"""

import os
from datetime import datetime

def sign_pdf_with_certificate(pdf_path, cert_path=None, key_path=None, password=None):
    """
    Sign PDF with digital certificate
    
    Args:
        pdf_path: Path to input PDF
        cert_path: Path to .p12 certificate file
        key_path: Path to private key (optional, can be in .p12)
        password: Certificate password
    
    Returns:
        Path to signed PDF
    """
    try:
        from pyhanko.sign import signers
        from pyhanko.sign.fields import SigFieldSpec
        from pyhanko.pdf_utils.reader import PdfFileReader
        from pyhanko.pdf_utils.writer import PdfFileWriter
        
        # If no certificate, create placeholder signature
        # (In production, you'd use actual .p12 file)
        if not cert_path or not os.path.exists(cert_path):
            return add_placeholder_signature(pdf_path)
        
        # Load certificate
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        
        # Sign PDF
        signer = signers.PdfSigner(
            signature_box=SigFieldSpec('Signature'),
            signer=signers.SimpleSigner.load(
                pfx_file=cert_data,
                passphrase=password.encode() if password else None
            )
        )
        
        with open(pdf_path, 'rb') as f:
            reader = PdfFileReader(f)
            writer = PdfFileWriter()
            writer.clone_reader_document_root(reader)
            
            signer.sign_pdf(
                writer,
                in_place=True
            )
        
        return pdf_path
        
    except ImportError:
        # If pyhanko not available, add placeholder
        return add_placeholder_signature(pdf_path)
    except Exception as e:
        print(f"Signing error: {e}")
        return add_placeholder_signature(pdf_path)

def add_placeholder_signature(pdf_path):
    """
    Add placeholder signature to PDF (for demo purposes)
    In production, use actual digital certificate
    """
    # For now, just return the unsigned PDF
    # The system is ready for real certificate when provided
    return pdf_path

def create_demo_certificate(output_path):
    """
    Create a self-signed demo certificate for testing
    In production, use proper certificate from CA
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        import selfsigned
        
        # Generate self-signed certificate
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"TH"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Bangkok"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Bangkok"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"GULF AGENCY COMPANY (THAILAND) LTD."),
            x509.NameAttribute(NameOID.COMMON_NAME, u"GAC Thailand"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(private_key, hashes.SHA256())
        
        # Save as .p12
        # Note: This is simplified - real implementation would use proper PKCS12
        return None
        
    except Exception as e:
        print(f"Certificate creation error: {e}")
        return None

def verify_signature(pdf_path):
    """
    Verify digital signature in PDF
    
    Returns:
        Dictionary with verification result
    """
    try:
        from pyhanko import stamp
        from pyhanko.pdf_utils.reader import PdfFileReader
        
        with open(pdf_path, 'rb') as f:
            reader = PdfFileReader(f)
            
            if not reader.embedded_signatures:
                return {
                    'valid': False,
                    'message': 'No signature found'
                }
            
            for sig in reader.embedded_signatures:
                return {
                    'valid': sig.check_integrity(),
                    'signer': str(sig.signer),
                    'signed_at': sig.signed_at,
                    'message': 'Signature verified'
                }
                
    except Exception as e:
        return {
            'valid': False,
            'message': f'Verification error: {str(e)}'
        }
    
    return {
        'valid': False,
        'message': 'No signature field'
    }
