"""
Custom Exception Classes for Telecom Dashboard

This module defines custom exception classes for better error handling
and debugging throughout the application.
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TelecomDashboardError(Exception):
    """Base exception class for all Telecom Dashboard related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize custom exception
        
        Args:
            message: Human readable error message
            error_code: Optional error code for categorization
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        
        # Log the exception when created
        logger.error(f"{self.__class__.__name__}: {message}", 
                    extra={'error_code': error_code, 'details': details})

class DatabaseError(TelecomDashboardError):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, query: Optional[str] = None, 
                 table: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if query:
            details['query'] = query
        if table:
            details['table'] = table
        kwargs['details'] = details
        super().__init__(message, error_code="DB_ERROR", **kwargs)

class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    
    def __init__(self, message: str = "Failed to connect to database", **kwargs):
        details = kwargs.pop('details', {})
        super().__init__(message, details=details)
        self.error_code = "DB_CONNECTION_ERROR"

class DatabaseQueryError(DatabaseError):
    """Raised when database query execution fails"""
    
    def __init__(self, message: str, query: str, **kwargs):
        details = kwargs.pop('details', {})
        super().__init__(message, query=query, details=details)
        self.error_code = "DB_QUERY_ERROR"

class DataValidationError(TelecomDashboardError):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)  # Convert to string for logging
        kwargs['details'] = details
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)

class ConfigurationError(TelecomDashboardError):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        kwargs['details'] = details
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)

class SecurityError(TelecomDashboardError):
    """Raised when security validation fails"""
    
    def __init__(self, message: str, security_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if security_type:
            details['security_type'] = security_type
        kwargs['details'] = details
        super().__init__(message, error_code="SECURITY_ERROR", **kwargs)

class AuthenticationError(SecurityError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        details = kwargs.pop('details', {})
        super().__init__(message, security_type="authentication", details=details)
        self.error_code = "AUTH_ERROR"

class AuthorizationError(SecurityError):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Authorization failed", **kwargs):
        details = kwargs.pop('details', {})
        super().__init__(message, security_type="authorization", details=details)
        self.error_code = "AUTHZ_ERROR"

class APIError(TelecomDashboardError):
    """Raised when external API calls fail"""
    
    def __init__(self, message: str, api_name: Optional[str] = None, 
                 status_code: Optional[int] = None, response_data: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if api_name:
            details['api_name'] = api_name
        if status_code:
            details['status_code'] = status_code
        if response_data:
            details['response_data'] = response_data
        kwargs['details'] = details
        super().__init__(message, error_code="API_ERROR", **kwargs)

class LLMServiceError(APIError):
    """Raised when LLM service operations fail"""
    
    def __init__(self, message: str, model: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if model:
            details['model'] = model
        kwargs['details'] = details
        super().__init__(message, api_name="llm_service", **kwargs)
        self.error_code = "LLM_ERROR"

class DataProcessingError(TelecomDashboardError):
    """Raised when data processing operations fail"""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 data_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if operation:
            details['operation'] = operation
        if data_type:
            details['data_type'] = data_type
        kwargs['details'] = details
        super().__init__(message, error_code="DATA_PROCESSING_ERROR", **kwargs)

class CacheError(TelecomDashboardError):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if cache_key:
            details['cache_key'] = cache_key
        kwargs['details'] = details
        super().__init__(message, error_code="CACHE_ERROR", **kwargs)

class UIError(TelecomDashboardError):
    """Raised when UI rendering fails"""
    
    def __init__(self, message: str, component: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if component:
            details['component'] = component
        kwargs['details'] = details
        super().__init__(message, error_code="UI_ERROR", **kwargs)

# Error recovery utilities
class ErrorRecovery:
    """Utilities for error recovery and graceful degradation"""
    
    @staticmethod
    def with_fallback(primary_func, fallback_func, *args, **kwargs):
        """
        Execute primary function with fallback on error
        
        Args:
            primary_func: Primary function to try
            fallback_func: Fallback function if primary fails
            *args: Arguments for both functions
            **kwargs: Keyword arguments for both functions
            
        Returns:
            Result from primary or fallback function
        """
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary function failed: {e}, trying fallback")
            return fallback_func(*args, **kwargs)
    
    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Retry function with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for backoff delay
            
        Returns:
            Function result or raises last exception
        """
        import time
        
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = backoff_factor * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")
            
            raise last_exception
        
        return wrapper
    
    @staticmethod
    def safe_execute(func, default_value=None, log_errors=True):
        """
        Execute function safely with default value on error
        
        Args:
            func: Function to execute
            default_value: Value to return on error
            log_errors: Whether to log errors
            
        Returns:
            Function result or default value
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Safe execution failed: {e}")
                return default_value
        
        return wrapper

# Exception handler decorator
def handle_exceptions(default_return=None, reraise_as=None):
    """
    Decorator to handle exceptions in functions
    
    Args:
        default_return: Default value to return on exception
        reraise_as: Exception class to reraise as
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if reraise_as:
                    raise reraise_as(f"Error in {func.__name__}: {str(e)}") from e
                else:
                    logger.error(f"Exception in {func.__name__}: {e}")
                    return default_return
        return wrapper
    return decorator
