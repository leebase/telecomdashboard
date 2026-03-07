"""
Centralized Configuration Management System

This module provides a unified interface for managing application configuration,
including database settings, UI preferences, security settings, and performance tuning.
"""

import os
import sys
import yaml
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConfigValidationError(Exception):
    """Configuration validation error"""
    message: str
    missing_vars: List[str] = field(default_factory=list)
    invalid_vars: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

class EnvironmentValidator:
    """
    Environment variable validation for production deployment
    
    Validates critical configuration before application startup
    """
    
    # Required environment variables for every environment
    REQUIRED_VARS = [
        'ENVIRONMENT',  # production, staging, development
        'LLM_API_KEY',  # AI functionality is a core product capability
    ]
    
    # Optional but recommended environment variables
    RECOMMENDED_VARS = [
        'LLM_API_KEY',           # AI functionality
        'DATABASE_URL',          # Production database
        'LOG_LEVEL',            # Logging configuration
        'CACHE_TTL_SECONDS',    # Performance tuning
        'FEATURE_STRUCTURED_LOGGING',  # Feature flags
    ]
    
    # Environment-specific requirements
    PRODUCTION_REQUIRED_VARS = [
        'DATABASE_URL',          # Must use production database
        'LLM_API_KEY',          # AI features required in production
        'LOG_LEVEL',            # Must specify logging level
    ]
    
    @classmethod
    def validate_environment(cls, environment: str = None) -> Dict[str, Any]:
        """
        Validate environment configuration
        
        Args:
            environment: Target environment (production, staging, development)
            
        Returns:
            Dict with validation results
            
        Raises:
            ConfigValidationError: If critical validation fails
        """
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development')
        
        results = {
            'environment': environment,
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_required': [],
            'missing_recommended': [],
            'summary': {}
        }
        
        # Check required variables
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                results['missing_required'].append(var)
                results['errors'].append(f"Missing required environment variable: {var}")
        
        # Check production-specific requirements
        if environment.lower() == 'production':
            for var in cls.PRODUCTION_REQUIRED_VARS:
                value = os.getenv(var)
                if not value:
                    results['missing_required'].append(var)
                    results['errors'].append(f"Missing production-required variable: {var}")
        
        # Check recommended variables
        for var in cls.RECOMMENDED_VARS:
            value = os.getenv(var)
            if not value:
                results['missing_recommended'].append(var)
                results['warnings'].append(f"Missing recommended variable: {var}")
        
        # Validate specific variables
        cls._validate_specific_vars(results)
        
        # Set overall validity
        results['valid'] = len(results['errors']) == 0

        unique_missing_required = set(results['missing_required'])
        unique_missing_recommended = set(results['missing_recommended'])
        
        # Generate summary
        results['summary'] = {
            'required_vars_set': len(cls.REQUIRED_VARS) - len([v for v in unique_missing_required if v in cls.REQUIRED_VARS]),
            'recommended_vars_set': len(cls.RECOMMENDED_VARS) - len(unique_missing_recommended),
            'total_errors': len(results['errors']),
            'total_warnings': len(results['warnings'])
        }
        
        return results
    
    @classmethod
    def _validate_specific_vars(cls, results: Dict[str, Any]):
        """Validate specific environment variable formats and values"""
        
        # Validate ENVIRONMENT
        environment = os.getenv('ENVIRONMENT', '').lower()
        if environment and environment not in ['production', 'staging', 'development', 'testing']:
            results['errors'].append(f"Invalid ENVIRONMENT value: {environment}. Must be one of: production, staging, development, testing")
        
        # Validate LOG_LEVEL
        log_level = os.getenv('LOG_LEVEL', '').upper()
        if log_level and log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            results['errors'].append(f"Invalid LOG_LEVEL value: {log_level}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        # Validate CACHE_TTL_SECONDS
        cache_ttl = os.getenv('CACHE_TTL_SECONDS')
        if cache_ttl:
            try:
                ttl_value = int(cache_ttl)
                if ttl_value < 0 or ttl_value > 3600:
                    results['warnings'].append(f"CACHE_TTL_SECONDS value {ttl_value} outside recommended range (0-3600)")
            except ValueError:
                results['errors'].append(f"Invalid CACHE_TTL_SECONDS value: {cache_ttl}. Must be an integer")
        
        # Validate DATABASE_URL format
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            if not any(database_url.startswith(prefix) for prefix in ['postgresql://', 'snowflake://', 'sqlite://', 'mysql://']):
                results['warnings'].append("DATABASE_URL format not recognized. Expected: postgresql://, snowflake://, sqlite://, or mysql://")
        
        # Validate LLM_API_KEY format
        api_key = os.getenv('LLM_API_KEY')
        if api_key:
            if not api_key.startswith(('sk-', 'pk-')) or len(api_key) < 20:
                results['warnings'].append("LLM_API_KEY format may be invalid. Expected format: sk-... or pk-... with 20+ characters")
    
    @classmethod
    def validate_startup_config(cls) -> bool:
        """
        Validate configuration at startup
        
        Returns:
            bool: True if validation passes, False otherwise
            
        Raises:
            ConfigValidationError: If critical validation fails
        """
        validation_results = cls.validate_environment()

        if validation_results['valid']:
            logger.info(f"✅ Environment validation passed for {validation_results['environment']} environment")
            for warning in validation_results['warnings']:
                logger.warning(f"⚠️ {warning}")
            return True

        logger.error(f"❌ Environment validation failed for {validation_results['environment']} environment")
        for error in validation_results['errors']:
            logger.error(f"🚨 {error}")

        raise ConfigValidationError(
            message=f"Environment validation failed with {len(validation_results['errors'])} errors",
            missing_vars=validation_results['missing_required'],
            invalid_vars=validation_results['errors'],
        )

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "data/telecom_db.sqlite"
    connection_timeout: int = 30000
    enable_foreign_keys: bool = True
    cache_size: int = 32
    trend_cache_size: int = 16

    def __post_init__(self) -> None:
        if not self.path.endswith((".sqlite", ".db")):
            raise ValueError("Database path must end with .sqlite or .db")
        if self.connection_timeout <= 0:
            raise ValueError("Database connection timeout must be positive")
        if self.cache_size < 1:
            raise ValueError("Database cache size must be at least 1")
        if self.trend_cache_size < 1:
            raise ValueError("Trend cache size must be at least 1")

@dataclass
class UIConfig:
    """User interface configuration settings"""
    default_theme: str = "verizon"
    page_title: str = "Telecom KPI Dashboard"
    page_icon: str = "📡"
    layout: str = "wide"
    sidebar_state: str = "expanded"
    show_debug_info: bool = False

    def __post_init__(self) -> None:
        if self.layout not in {"wide", "centered"}:
            raise ValueError("Layout must be either 'wide' or 'centered'")
        if self.sidebar_state not in {"expanded", "collapsed", "auto"}:
            raise ValueError("Sidebar state must be one of: expanded, collapsed, auto")

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    enable_security_logging: bool = True
    log_file: str = "security.log"

    def __post_init__(self) -> None:
        if not 1 <= self.max_requests_per_minute <= 1000:
            raise ValueError("Max requests per minute must be between 1 and 1000")

@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    max_dataframe_rows: int = 10000
    enable_lazy_loading: bool = True
    concurrent_requests: int = 5

    def __post_init__(self) -> None:
        if self.cache_ttl_seconds < 0:
            raise ValueError("Cache TTL cannot be negative")
        if self.max_dataframe_rows < 100:
            raise ValueError("Max dataframe rows must be at least 100")
        if self.concurrent_requests < 1:
            raise ValueError("Concurrent requests must be at least 1")

@dataclass
class AIConfig:
    """AI/LLM configuration settings"""
    model: str = "google/gemini-2.5-flash"
    temperature: float = 0.1
    max_tokens: int = 2000
    api_timeout: int = 30
    enable_insights: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.temperature <= 2:
            raise ValueError("AI temperature must be between 0 and 2")
        if not 100 <= self.max_tokens <= 10000:
            raise ValueError("AI max tokens must be between 100 and 10000")
        if self.api_timeout <= 0:
            raise ValueError("AI API timeout must be positive")

@dataclass
class FeatureConfig:
    """Feature flag configuration"""
    # AI and ML Features
    ai_insights: bool = True
    ai_insights_beta: bool = False
    pii_scrubbing: bool = True
    
    # Performance Features
    cache_ttl: bool = True
    circuit_breaker: bool = True
    connection_pooling: bool = True
    
    # Enterprise Features
    structured_logging: bool = False
    snowflake_query_tagging: bool = True
    health_checks_detailed: bool = True
    
    # UI and UX Features
    theme_switching: bool = True
    benchmark_management: bool = True
    print_mode: bool = True
    
    # Security Features
    security_headers: bool = True
    rate_limiting: bool = True
    sql_injection_protection: bool = True
    
    # Development Features
    debug_mode: bool = False
    test_mode: bool = False
    performance_monitoring: bool = True

@dataclass
class AppConfig:
    """Main application configuration"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration values"""
        DatabaseConfig(**vars(self.database))
        UIConfig(**vars(self.ui))
        SecurityConfig(**vars(self.security))
        PerformanceConfig(**vars(self.performance))
        AIConfig(**vars(self.ai))

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.yaml"
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self._config: Optional[AppConfig] = None
        
    @property
    def config(self) -> AppConfig:
        """Get current configuration, loading if necessary"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def load_config(self) -> AppConfig:
        """Load configuration from file or create default"""
        config_path = self.config_dir / self.config_file
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
                return self._create_config_from_dict(config_data)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                logger.info("Using default configuration")
        
        # Return default configuration
        return self._create_config_from_dict({})

    @staticmethod
    def _coerce_feature_flag(value: str) -> bool:
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"Invalid feature flag value: {value}")
    
    def save_config(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file"""
        config = config or self.config
        config_path = self.config_dir / self.config_file
        
        try:
            config_dict = self._config_to_dict(config)
            with open(config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> AppConfig:
        """Create AppConfig from dictionary"""
        database_defaults = vars(DatabaseConfig())
        ui_defaults = vars(UIConfig())
        security_defaults = vars(SecurityConfig())
        performance_defaults = vars(PerformanceConfig())
        ai_defaults = vars(AIConfig())
        feature_defaults = vars(FeatureConfig())

        config = AppConfig(
            database=DatabaseConfig(**{
                key: value
                for key, value in {**database_defaults, **config_data.get('database', {})}.items()
                if key in database_defaults
            }),
            ui=UIConfig(**{
                key: value
                for key, value in {**ui_defaults, **config_data.get('ui', {})}.items()
                if key in ui_defaults
            }),
            security=SecurityConfig(**{
                key: value
                for key, value in {**security_defaults, **config_data.get('security', {})}.items()
                if key in security_defaults
            }),
            performance=PerformanceConfig(**{
                key: value
                for key, value in {**performance_defaults, **config_data.get('performance', {})}.items()
                if key in performance_defaults
            }),
            ai=AIConfig(**{
                key: value
                for key, value in {**ai_defaults, **config_data.get('ai', {})}.items()
                if key in ai_defaults
            }),
            features=FeatureConfig(**{
                key: value
                for key, value in {**feature_defaults, **config_data.get('features', {})}.items()
                if key in feature_defaults
            }),
        )

        for key in feature_defaults:
            env_var = f"FEATURE_{key.upper()}"
            env_value = os.getenv(env_var)
            if env_value is None:
                continue
            setattr(config.features, key, self._coerce_feature_flag(env_value))

        config._validate_config()
        return config
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """Convert AppConfig to dictionary"""
        return {
            'database': {
                'path': config.database.path,
                'connection_timeout': config.database.connection_timeout,
                'enable_foreign_keys': config.database.enable_foreign_keys,
                'cache_size': config.database.cache_size,
                'trend_cache_size': config.database.trend_cache_size,
            },
            'ui': {
                'default_theme': config.ui.default_theme,
                'page_title': config.ui.page_title,
                'page_icon': config.ui.page_icon,
                'layout': config.ui.layout,
                'sidebar_state': config.ui.sidebar_state,
                'show_debug_info': config.ui.show_debug_info,
            },
            'security': {
                'enable_rate_limiting': config.security.enable_rate_limiting,
                'max_requests_per_minute': config.security.max_requests_per_minute,
                'enable_input_validation': config.security.enable_input_validation,
                'enable_output_sanitization': config.security.enable_output_sanitization,
                'enable_security_logging': config.security.enable_security_logging,
                'log_file': config.security.log_file,
            },
            'performance': {
                'enable_caching': config.performance.enable_caching,
                'cache_ttl_seconds': config.performance.cache_ttl_seconds,
                'max_dataframe_rows': config.performance.max_dataframe_rows,
                'enable_lazy_loading': config.performance.enable_lazy_loading,
                'concurrent_requests': config.performance.concurrent_requests,
            },
            'ai': {
                'model': config.ai.model,
                'temperature': config.ai.temperature,
                'max_tokens': config.ai.max_tokens,
                'api_timeout': config.ai.api_timeout,
                'enable_insights': config.ai.enable_insights,
            },
            'features': {
                'ai_insights': config.features.ai_insights,
                'ai_insights_beta': config.features.ai_insights_beta,
                'pii_scrubbing': config.features.pii_scrubbing,
                'cache_ttl': config.features.cache_ttl,
                'circuit_breaker': config.features.circuit_breaker,
                'connection_pooling': config.features.connection_pooling,
                'structured_logging': config.features.structured_logging,
                'snowflake_query_tagging': config.features.snowflake_query_tagging,
                'health_checks_detailed': config.features.health_checks_detailed,
                'theme_switching': config.features.theme_switching,
                'benchmark_management': config.features.benchmark_management,
                'print_mode': config.features.print_mode,
                'security_headers': config.features.security_headers,
                'rate_limiting': config.features.rate_limiting,
                'sql_injection_protection': config.features.sql_injection_protection,
                'debug_mode': config.features.debug_mode,
                'test_mode': config.features.test_mode,
                'performance_monitoring': config.features.performance_monitoring,
            }
        }
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.config.database
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration"""
        return self.config.ui
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.config.security
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration"""
        return self.config.performance
    
    def get_ai_config(self) -> AIConfig:
        """Get AI configuration"""
        return self.config.ai
    
    def update_config(self, **kwargs) -> None:
        """Update configuration values"""
        config = self.config
        
        for section, values in kwargs.items():
            if hasattr(config, section):
                section_config = getattr(config, section)
                for key, value in values.items():
                    if hasattr(section_config, key):
                        setattr(section_config, key, value)
                    else:
                        logger.warning(f"Unknown config key: {section}.{key}")
            else:
                logger.warning(f"Unknown config section: {section}")
        
        # Re-validate after updates
        config._validate_config()
        self.save_config(config)
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self._config = AppConfig()
        self.save_config()
        logger.info("Configuration reset to defaults")

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> AppConfig:
    """Get global configuration instance"""
    return config_manager.config

def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return config_manager.get_database_config()

def get_ui_config() -> UIConfig:
    """Get UI configuration"""
    return config_manager.get_ui_config()

def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return config_manager.get_security_config()

def get_performance_config() -> PerformanceConfig:
    """Get performance configuration"""
    return config_manager.get_performance_config()

def get_ai_config() -> AIConfig:
    """Get AI configuration"""
    return config_manager.get_ai_config()
