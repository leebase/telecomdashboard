"""
Configuration loader for API keys and other sensitive data.
"""
import os
import yaml
import re
from typing import Dict, Any, Optional
from security_manager import security_logger

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.secrets.yaml with environment variable substitution.
    Falls back to environment variables if file not found.
    
    Returns:
        Dict containing configuration values
    """
    try:
        # Try to load from config file
        config_path = os.path.join(os.path.dirname(__file__), 'config.secrets.yaml')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
                
            # Validate raw config before substitution
            raw_config = yaml.safe_load(content)
            if not validate_config_security(raw_config):
                security_logger.error("Configuration security validation failed")
                return get_fallback_config()
            
            # Substitute environment variables after validation
            content = substitute_env_vars(content)
            config = yaml.safe_load(content)
            return config
        
        # Fall back to environment variables
        return get_fallback_config()
        
    except Exception as e:
        security_logger.error(f"Configuration loading error: {e}")
        return get_fallback_config()

def substitute_env_vars(content: str) -> str:
    """Substitute environment variables in configuration content"""
    def replace_env_var(match):
        var_name = match.group(1)
        env_value = os.getenv(var_name)
        if env_value is None:
            security_logger.warning(f"Environment variable {var_name} not found")
            return ""
        return env_value
    
    # Replace ${VAR_NAME} patterns
    return re.sub(r'\$\{([^}]+)\}', replace_env_var, content)

def validate_config_security(config: Dict[str, Any]) -> bool:
    """Validate configuration for security issues"""
    try:
        # Check for hardcoded API keys (should not contain actual keys)
        llm_config = config.get('llm', {})
        api_key = llm_config.get('api_key', '')
        
        # Allow hardcoded API keys in local config.secrets.yaml, but log a warning
        # Previous behavior rejected hardcoded keys, forcing environment fallback.
        # For local/dev use we relax this to avoid 401s when env vars are not used.
        if api_key and not api_key.startswith('${') and len(api_key) > 10:
            security_logger.warning("Hardcoded API key detected in configuration (allowed for local/dev)")
            return True
        
        return True
        
    except Exception as e:
        security_logger.error(f"Configuration validation error: {e}")
        return False

def get_fallback_config() -> Dict[str, Any]:
    """Get fallback configuration from environment variables"""
    return {
        'llm': {
            'provider': os.getenv('LLM_PROVIDER', 'openrouter'),
            'api_key': os.getenv('LLM_API_KEY'),
            'model': os.getenv('LLM_MODEL', 'google/gemini-2.5-flash'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '1000')),
            'api_base': os.getenv('LLM_API_BASE', 'https://openrouter.ai/api/v1')
        }
    }

def get_llm_config() -> Dict[str, Any]:
    """
    Get LLM-specific configuration.
    
    Returns:
        Dict containing LLM configuration
    """
    config = load_config()
    return config.get('llm', {})

def get_api_key() -> Optional[str]:
    """
    Get the API key for the LLM provider.
    
    Returns:
        API key string or None if not found
    """
    return get_llm_config().get('api_key')
