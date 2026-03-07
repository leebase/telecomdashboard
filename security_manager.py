"""
Security Manager for Telecom KPI Dashboard
Implements comprehensive security best practices for web database applications
"""

import os
import re
import hashlib
import secrets
import html
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import sqlite3
from functools import wraps
import streamlit as st

# Configure security logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security.log'),
        logging.StreamHandler()
    ]
)

security_logger = logging.getLogger('security')

class SecurityManager:
    """Centralized security manager for the application"""
    
    def __init__(self):
        self.failed_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        
    def validate_input(self, input_data: Any, input_type: str = "string") -> bool:
        """
        Validate and sanitize user input
        
        Args:
            input_data: Data to validate
            input_type: Type of input (string, numeric, email, etc.)
            
        Returns:
            Boolean indicating if input is valid
        """
        try:
            if input_data is None:
                return False
                
            # Skip strict validation for AI prompts
            if input_type == "ai_prompt":
                return self._validate_ai_prompt(input_data)
                
            # Basic SQL injection patterns (for database queries)
            sql_patterns = [
                r"union\s+select", r"drop\s+table", r"delete\s+from", 
                r"insert\s+into", r"update\s+set", r"create\s+table",
                r"alter\s+table", r"exec\s*\(", r"execute\s*\(",
                r"sp_", r"xp_", r"--\s*$", r";\s*drop", r"/\*.*\*/.*union"
            ]
            
            # XSS patterns
            xss_patterns = [
                r"<script", r"javascript:", r"onload=", r"onerror=",
                r"onclick=", r"onmouseover=", r"vbscript:", r"data:text/html"
            ]
            
            input_str = str(input_data).lower()
            
            # Check for SQL injection
            for pattern in sql_patterns:
                if re.search(pattern, input_str, re.IGNORECASE):
                    security_logger.warning(f"SQL injection attempt detected: {pattern}")
                    return False
            
            # Check for XSS
            for pattern in xss_patterns:
                if re.search(pattern, input_str, re.IGNORECASE):
                    security_logger.warning(f"XSS attempt detected: {pattern}")
                    return False
            
            # Type-specific validation
            if input_type == "numeric":
                try:
                    float(input_data)
                except (ValueError, TypeError):
                    return False
            
            elif input_type == "email":
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(input_data)):
                    return False
            
            return True
            
        except Exception as e:
            security_logger.error(f"Input validation error: {e}")
            return False
    
    def _validate_ai_prompt(self, prompt: str) -> bool:
        """
        Validate AI prompts with relaxed security rules
        
        Args:
            prompt: The AI prompt to validate
            
        Returns:
            Boolean indicating if prompt is valid
        """
        try:
            # Basic checks for AI prompts
            if len(str(prompt)) > 10000:  # Reasonable length limit
                security_logger.warning("AI prompt too long")
                return False
                
            # Only check for dangerous SQL patterns (not common text patterns)
            dangerous_patterns = [
                r"union\s+select.*from", r"drop\s+table", r"delete\s+from.*where", 
                r"insert\s+into.*values", r"update.*set.*where", r"create\s+table",
                r"alter\s+table", r"exec\s*\(", r"execute\s*\(",
                r"\bor\s+1\s*=\s*1\b", r"select\s+\*\s+from\s+passwords",
                r"(?:^|[;|&])\s*(?:cat|grep|curl|wget)\b",
                r"\.\./", r"\.\.\\", r"/etc/passwd", r"system32\\config\\sam",
                r"<script\b", r"javascript:", r"document\.cookie",
                r"db\.collection\.find", r'"\$gt"\s*:', r"\$gt\s*:",
                r"\)\(uid=\*\)", r"\*\)\(&\(password=\*\)\)",
                r"ignore\s+all\s+previous\s+instructions",
                r"disregard\s+safety\s+guidelines",
                r"forget\s+everything\s+above",
                r"previous\s+conversation\s+never\s+happened",
                r"\boverride\s*:",
                r"jailbreak\s+mode",
                r"\[inst\].*\[/inst\]",
                r"human:\s*ignore",
                r"system:\s*disregard",
                r"\bas\s+an\s+admin\b.*ignore",
                r"reveal\s+secrets",
                r"show\s+internal\s+system\s+information",
                r"give\s+me\s+admin\s+access",
                r"print\s+all\s+environment\s+variables"
            ]
            
            prompt_str = str(prompt).lower()
            for pattern in dangerous_patterns:
                if re.search(pattern, prompt_str, re.IGNORECASE):
                    security_logger.warning(f"Potentially dangerous pattern in AI prompt: {pattern}")
                    return False
                    
            return True
            
        except Exception as e:
            security_logger.error(f"AI prompt validation error: {e}")
            return False
    
    def sanitize_output(self, data: str) -> str:
        """
        Sanitize output data to prevent XSS
        
        Args:
            data: String to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(data, str):
            data = str(data)
        
        # HTML escape
        sanitized = html.escape(data)
        
        # Additional sanitization for potential bypasses
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'data:text/html', 'data:text/plain', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def secure_database_query(self, query: str, params: tuple = None) -> bool:
        """
        Validate database queries for security
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Boolean indicating if query is safe
        """
        # Ensure parameterized queries
        if params is None and ('?' in query or '%s' in query):
            security_logger.error("Non-parameterized query detected")
            return False
        
        # Check for dangerous SQL operations
        dangerous_operations = [
            'drop table', 'truncate table', 'delete from', 
            'alter table', 'create table', 'grant', 'revoke'
        ]
        
        query_lower = query.lower().strip()
        for operation in dangerous_operations:
            if operation in query_lower:
                security_logger.warning(f"Potentially dangerous SQL operation: {operation}")
                return False
        
        return True
    
    def rate_limit_check(self, identifier: str) -> bool:
        """
        Check if request should be rate limited
        
        Args:
            identifier: Unique identifier (IP, user, etc.)
            
        Returns:
            Boolean indicating if request is allowed
        """
        current_time = datetime.now()
        
        if identifier in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[identifier]
            
            # Reset if lockout period has passed
            if current_time - last_attempt > self.lockout_duration:
                del self.failed_attempts[identifier]
                return True
            
            # Check if max attempts exceeded
            if attempts >= self.max_attempts:
                security_logger.warning(f"Rate limit exceeded for {identifier}")
                return False
        
        return True
    
    def log_failed_attempt(self, identifier: str):
        """Log a failed attempt for rate limiting"""
        current_time = datetime.now()
        
        if identifier in self.failed_attempts:
            attempts, _ = self.failed_attempts[identifier]
            self.failed_attempts[identifier] = (attempts + 1, current_time)
        else:
            self.failed_attempts[identifier] = (1, current_time)

def secure_query_executor(func):
    """Decorator for secure database query execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        security_manager = SecurityManager()
        
        # Log the operation
        security_logger.info(f"Database operation: {func.__name__}")
        
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            security_logger.error(f"Database error in {func.__name__}: {e}")
            raise
        except Exception as e:
            security_logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    
    return wrapper

def validate_environment_config():
    """Validate environment configuration for security"""
    required_vars = ['LLM_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        security_logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    return True

def sanitize_streamlit_output(text: str) -> str:
    """
    Safely sanitize text for Streamlit display
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for display
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Remove potentially dangerous content
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)
    
    # HTML encode dangerous characters but preserve basic formatting
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    return text

def secure_file_access(file_path: str) -> bool:
    """
    Validate file access for security
    
    Args:
        file_path: Path to file
        
    Returns:
        Boolean indicating if access is safe
    """
    # Prevent path traversal attacks
    if '..' in file_path or file_path.startswith('/'):
        security_logger.warning(f"Path traversal attempt: {file_path}")
        return False
    
    # Only allow access to specific directories
    allowed_directories = ['data/', 'styles/', 'docs/']
    
    if not any(file_path.startswith(dir_path) for dir_path in allowed_directories):
        security_logger.warning(f"Unauthorized file access attempt: {file_path}")
        return False
    
    return True

def get_security_headers() -> Dict[str, str]:
    """Get security headers for HTTP responses"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    }

# Global security manager instance
security_manager = SecurityManager()
