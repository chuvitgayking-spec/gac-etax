"""
Error Handling Utilities
Standardized error handling for the application
"""
import traceback
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger('etax')


@dataclass
class ETaxError(Exception):
    """Base exception for E-Tax system"""
    message: str
    error_code: str = 'ETAX_ERROR'
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"


@dataclass 
class XMLValidationError(ETaxError):
    """XML validation failed"""
    error_code: str = 'XML_VALIDATION_ERROR'


@dataclass
class DatabaseError(ETaxError):
    """Database operation failed"""
    error_code: str = 'DATABASE_ERROR'


@dataclass
class SignatureError(ETaxError):
    """Digital signature failed"""
    error_code: str = 'SIGNATURE_ERROR'


@dataclass
class DeliveryError(ETaxError):
    """Delivery to RD or email failed"""
    error_code: str = 'DELIVERY_ERROR'


class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_error(
        error: Exception,
        context: str = '',
        reraise: bool = False
    ) -> Dict[str, Any]:
        """
        Handle error and return standardized response
        
        Args:
            error: The exception
            context: Where the error occurred
            reraise: Whether to re-raise after handling
        
        Returns:
            Error details dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        tb = traceback.format_exc()
        
        # Log error
        logger.error(
            f"Error in {context}: {error_type} - {error_message}\n{tb}"
        )
        
        # Build response
        error_details = {
            'success': False,
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add specific error codes
        if isinstance(error, ETaxError):
            error_details['error_code'] = error.error_code
            error_details['details'] = error.details
        
        if reraise:
            raise error
        
        return error_details
    
    @staticmethod
    def safe_execute(func, *args, default=None, context: str = '', **kwargs):
        """
        Execute function with error handling
        
        Args:
            func: Function to execute
            *args: Positional arguments
            default: Default value on error
            context: Context description
            **kwargs: Keyword arguments
        
        Returns:
            Function result or default value
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_error(e, context=context)
            return default


def validate_required_fields(data: Dict, required: list, context: str = '') -> None:
    """
    Validate required fields exist
    
    Args:
        data: Data dictionary
        required: List of required field names
        context: Context for error message
    
    Raises:
        ValueError: If required field is missing
    """
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise ValueError(
            f"Missing required fields in {context}: {', '.join(missing)}"
        )
