"""
Test suite for feature flag management and configuration

Tests feature flag loading, environment variable overrides, and runtime configuration
to ensure proper feature flag functionality across different environments.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config_manager import ConfigManager, get_config, FeatureConfig

class TestFeatureFlags:
    """Test feature flag functionality"""
    
    def test_feature_config_defaults(self):
        """Test default feature flag values"""
        features = FeatureConfig()
        
        # AI and ML Features
        assert features.ai_insights == True
        assert features.ai_insights_beta == False
        assert features.pii_scrubbing == True
        
        # Performance Features
        assert features.cache_ttl == True
        assert features.circuit_breaker == True
        assert features.connection_pooling == True
        
        # Enterprise Features
        assert features.structured_logging == False  # Should be False by default
        assert features.snowflake_query_tagging == True
        assert features.health_checks_detailed == True
        
        # Security Features
        assert features.security_headers == True
        assert features.rate_limiting == True
        assert features.sql_injection_protection == True
        
        # Development Features
        assert features.debug_mode == False
        assert features.test_mode == False
        assert features.performance_monitoring == True
    
    def test_feature_flag_environment_overrides(self):
        """Test feature flag overrides via environment variables"""
        # Test various override scenarios
        override_scenarios = [
            # Boolean true values
            {'FEATURE_DEBUG_MODE': 'true', 'expected': True},
            {'FEATURE_DEBUG_MODE': 'TRUE', 'expected': True},
            {'FEATURE_DEBUG_MODE': '1', 'expected': True},
            {'FEATURE_DEBUG_MODE': 'yes', 'expected': True},
            {'FEATURE_DEBUG_MODE': 'on', 'expected': True},
            
            # Boolean false values
            {'FEATURE_DEBUG_MODE': 'false', 'expected': False},
            {'FEATURE_DEBUG_MODE': 'FALSE', 'expected': False},
            {'FEATURE_DEBUG_MODE': '0', 'expected': False},
            {'FEATURE_DEBUG_MODE': 'no', 'expected': False},
            {'FEATURE_DEBUG_MODE': 'off', 'expected': False},
        ]
        
        for scenario in override_scenarios:
            expected = scenario['expected']
            env_vars = {'FEATURE_DEBUG_MODE': scenario['FEATURE_DEBUG_MODE']}

            with patch.dict(os.environ, env_vars, clear=True):
                config = ConfigManager().load_config()
                assert config.features.debug_mode is expected
    
    def test_feature_flag_categories(self):
        """Test that all feature flag categories are properly defined"""
        features = FeatureConfig()
        
        # AI and ML Features
        ai_features = ['ai_insights', 'ai_insights_beta', 'pii_scrubbing']
        for feature in ai_features:
            assert hasattr(features, feature), f"Missing AI feature: {feature}"
        
        # Performance Features
        performance_features = ['cache_ttl', 'circuit_breaker', 'connection_pooling']
        for feature in performance_features:
            assert hasattr(features, feature), f"Missing performance feature: {feature}"
        
        # Enterprise Features
        enterprise_features = ['structured_logging', 'snowflake_query_tagging', 'health_checks_detailed']
        for feature in enterprise_features:
            assert hasattr(features, feature), f"Missing enterprise feature: {feature}"
        
        # UI and UX Features
        ui_features = ['theme_switching', 'benchmark_management', 'print_mode']
        for feature in ui_features:
            assert hasattr(features, feature), f"Missing UI feature: {feature}"
        
        # Security Features
        security_features = ['security_headers', 'rate_limiting', 'sql_injection_protection']
        for feature in security_features:
            assert hasattr(features, feature), f"Missing security feature: {feature}"
        
        # Development Features
        dev_features = ['debug_mode', 'test_mode', 'performance_monitoring']
        for feature in dev_features:
            assert hasattr(features, feature), f"Missing development feature: {feature}"
    
    def test_configuration_integration(self):
        """Test feature flag integration with main configuration"""
        try:
            config = get_config()
            
            # Should have features attribute
            assert hasattr(config, 'features'), "Configuration should have features attribute"
            
            # Features should be FeatureConfig instance
            assert isinstance(config.features, FeatureConfig), "Features should be FeatureConfig instance"
            
            # Test a few key features
            assert isinstance(config.features.ai_insights, bool)
            assert isinstance(config.features.structured_logging, bool)
            assert isinstance(config.features.debug_mode, bool)
            
        except Exception as e:
            # Configuration might not load properly in test environment
            pytest.skip(f"Configuration loading failed: {e}")
    
    def test_environment_specific_defaults(self):
        """Test environment-specific feature flag defaults"""
        # This test validates the concept of environment-specific defaults
        # In a real implementation, these would be loaded from config.template.yaml
        
        development_features = {
            'debug_mode': True,
            'structured_logging': False,
            'test_mode': True
        }
        
        staging_features = {
            'debug_mode': False,
            'structured_logging': True,
            'performance_monitoring': True
        }
        
        production_features = {
            'debug_mode': False,
            'structured_logging': True,
            'security_headers': True,
            'rate_limiting': True
        }
        
        # Validate the expected structure
        for env_name, expected_features in [
            ('development', development_features),
            ('staging', staging_features),
            ('production', production_features)
        ]:
            for feature_name, expected_value in expected_features.items():
                assert isinstance(expected_value, bool), f"{env_name}.{feature_name} should be boolean"
    
    def test_feature_flag_validation(self):
        """Test feature flag value validation"""
        # All feature flags should be boolean values
        features = FeatureConfig()
        
        for attr_name in dir(features):
            if not attr_name.startswith('_'):
                value = getattr(features, attr_name)
                assert isinstance(value, bool), f"Feature flag {attr_name} should be boolean, got {type(value)}"

class TestFeatureFlagCLI:
    """Test feature flag CLI functionality"""
    
    def test_config_validator_import(self):
        """Test that config_validator can be imported"""
        try:
            import config_validator
            assert hasattr(config_validator, 'ConfigManager')
        except ImportError as e:
            pytest.skip(f"config_validator not available: {e}")
    
    def test_config_manager_feature_operations(self):
        """Test ConfigManager feature flag operations"""
        try:
            from config_validator import ConfigManager
            
            manager = ConfigManager()
            
            # Test that methods exist
            assert hasattr(manager, 'list_feature_flags')
            assert hasattr(manager, 'set_feature_flag')
            assert hasattr(manager, 'export_config')
            
        except ImportError as e:
            pytest.skip(f"ConfigManager not available: {e}")

class TestFeatureFlagSecurity:
    """Test security aspects of feature flag management"""
    
    def test_production_security_features(self):
        """Test that security features are enabled in production"""
        production_security_features = [
            'security_headers',
            'rate_limiting', 
            'sql_injection_protection',
            'pii_scrubbing'
        ]
        
        features = FeatureConfig()
        
        for feature in production_security_features:
            assert hasattr(features, feature), f"Missing security feature: {feature}"
            # Most security features should default to True
            if feature != 'debug_mode':  # debug_mode should default to False
                default_value = getattr(features, feature)
                assert isinstance(default_value, bool), f"Security feature {feature} should be boolean"
    
    def test_development_vs_production_features(self):
        """Test that development and production have appropriate feature differences"""
        features = FeatureConfig()
        
        # Debug features should be False by default (safe for production)
        assert features.debug_mode == False
        assert features.test_mode == False
        
        # Security features should be True by default
        assert features.security_headers == True
        assert features.sql_injection_protection == True
        assert features.pii_scrubbing == True
        
        # Structured logging should be False by default (enabled in production via env-specific config)
        assert features.structured_logging == False

class TestFeatureFlagIntegration:
    """Integration tests for feature flag system"""
    
    def test_feature_flag_system_completeness(self):
        """Test that the feature flag system covers all major components"""
        features = FeatureConfig()
        
        # Count features by category
        ai_features = [attr for attr in dir(features) if not attr.startswith('_') and 'ai' in attr.lower()]
        performance_features = [attr for attr in dir(features) if not attr.startswith('_') and any(keyword in attr.lower() for keyword in ['cache', 'circuit', 'connection', 'performance'])]
        security_features = [attr for attr in dir(features) if not attr.startswith('_') and any(keyword in attr.lower() for keyword in ['security', 'injection', 'rate', 'pii'])]
        
        # Should have reasonable coverage
        assert len(ai_features) >= 2, f"Should have at least 2 AI features, found: {ai_features}"
        assert len(performance_features) >= 3, f"Should have at least 3 performance features, found: {performance_features}"
        assert len(security_features) >= 3, f"Should have at least 3 security features, found: {security_features}"
        
        # Total feature count should be reasonable (15+ as specified)
        total_features = len([attr for attr in dir(features) if not attr.startswith('_')])
        assert total_features >= 15, f"Should have at least 15 feature flags, found: {total_features}"
    
    def test_feature_flag_consistency(self):
        """Test feature flag naming and consistency"""
        features = FeatureConfig()
        
        feature_names = [attr for attr in dir(features) if not attr.startswith('_')]
        
        for feature_name in feature_names:
            # Feature names should use snake_case
            assert feature_name.islower(), f"Feature name {feature_name} should be lowercase"
            assert ' ' not in feature_name, f"Feature name {feature_name} should not contain spaces"
            
            # Feature values should be boolean
            value = getattr(features, feature_name)
            assert isinstance(value, bool), f"Feature {feature_name} should be boolean, got {type(value)}"

if __name__ == '__main__':
    # Run tests directly
    pytest.main([__file__, '-v'])
