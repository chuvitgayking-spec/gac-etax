"""
Configuration Loader
Loads environment variables and provides configuration to the app
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file if exists
ENV_PATH = Path(__file__).parent.parent / '.env'
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Config:
    """Application configuration"""
    
    # Database
    DB_PATH = os.getenv('DB_PATH', './data/invoices.db')
    
    # Company Info
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'GULF AGENCY COMPANY (THAILAND) LTD.')
    COMPANY_TAX_ID = os.getenv('COMPANY_TAX_ID', '0105535169497')
    COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', '')
    COMPANY_TEL = os.getenv('COMPANY_TEL', '')
    COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', '')
    COMPANY_BRANCH = os.getenv('COMPANY_BRANCH', '00000')
    
    # Tax Settings
    DEFAULT_VAT_RATE = float(os.getenv('DEFAULT_VAT_RATE', '0.07'))
    VAT_INCLUDED = os.getenv('VAT_INCLUDED', 'true').lower() == 'true'
    
    # RD Gateway
    RD_API_URL = os.getenv('RD_API_URL', '')
    RD_CLIENT_ID = os.getenv('RD_CLIENT_ID', '')
    RD_CLIENT_SECRET = os.getenv('RD_CLIENT_SECRET', '')
    
    # Email
    SMTP_SERVER = os.getenv('SMTP_SERVER', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    
    # HSM
    HSM_ENABLED = os.getenv('HSM_ENABLED', 'false').lower() == 'true'
    HSM_PRIVATE_KEY_PATH = os.getenv('HSM_PRIVATE_KEY_PATH', '')
    HSM_CERT_PATH = os.getenv('HSM_CERT_PATH', '')
    
    # Streamlit
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/etax.log')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    @classmethod
    def get_db_path(cls) -> str:
        """Get absolute database path"""
        if os.path.isabs(cls.DB_PATH):
            return cls.DB_PATH
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), cls.DB_PATH)
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert config to dictionary"""
        return {k: v for k, v in cls.__dict__.items() 
                if k.startswith('COMPANY_') or k.startswith('DEFAULT_')}


# Convenience function
def get_config() -> Config:
    return Config()
