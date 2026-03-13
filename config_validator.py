#!/usr/bin/env python3
"""
Configuration Validator and Management Utility

Standalone tool for validating environment configuration and managing
feature flags for the Telecom Dashboard application.
"""

import os
import sys
import argparse
import json
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import EnvironmentValidator, ConfigValidationError, get_config

class ConfigManager:
    """Configuration management and validation utility"""
    
    def __init__(self):
        self.validator = EnvironmentValidator()
    
    def validate_environment(self, environment: str = None, verbose: bool = False) -> bool:
        """Validate environment configuration"""
        try:
            results = self.validator.validate_environment(environment)
            
            print(f"🔍 Environment Validation Report")
            print(f"{'='*50}")
            print(f"Environment: {results['environment']}")
            print(f"Status: {'✅ VALID' if results['valid'] else '❌ INVALID'}")
            print(f"Errors: {len(results['errors'])}")
            print(f"Warnings: {len(results['warnings'])}")
            
            if results['errors']:
                print(f"\n🚨 Errors:")
                for error in results['errors']:
                    print(f"  - {error}")
            
            if results['warnings'] and verbose:
                print(f"\n⚠️  Warnings:")
                for warning in results['warnings']:
                    print(f"  - {warning}")
            
            # Summary
            summary = results['summary']
            print(f"\n📊 Summary:")
            print(f"  Required vars set: {summary['required_vars_set']}/{len(self.validator.REQUIRED_PRODUCTION_VARS)}")
            print(f"  Recommended vars set: {summary['recommended_vars_set']}/{len(self.validator.RECOMMENDED_VARS)}")
            
            return results['valid']
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def list_feature_flags(self) -> None:
        """List all available feature flags and their current values"""
        try:
            config = get_config()
            
            print(f"🎛️  Feature Flags Configuration")
            print(f"{'='*50}")
            
            if not hasattr(config, 'features'):
                print("❌ Feature flags not configured")
                return
            
            features = config.features
            
            # Group features by category
            categories = {
                'AI and ML Features': ['ai_insights', 'ai_insights_beta', 'pii_scrubbing'],
                'Performance Features': ['cache_ttl', 'circuit_breaker', 'connection_pooling'],
                'Enterprise Features': ['structured_logging', 'snowflake_query_tagging', 'health_checks_detailed'],
                'UI and UX Features': ['theme_switching', 'benchmark_management', 'print_mode'],
                'Security Features': ['security_headers', 'rate_limiting', 'sql_injection_protection'],
                'Development Features': ['debug_mode', 'test_mode', 'performance_monitoring']
            }
            
            for category, feature_list in categories.items():
                print(f"\n📋 {category}:")
                for feature in feature_list:
                    if hasattr(features, feature):
                        value = getattr(features, feature)
                        status = "✅ ON" if value else "❌ OFF"
                        env_var = f"FEATURE_{feature.upper()}"
                        override = " (ENV)" if os.getenv(env_var) else ""
                        print(f"  {feature:<25} {status}{override}")
            
            # Show environment variable overrides
            env_overrides = []
            for key in dir(features):
                if not key.startswith('_'):
                    env_var = f"FEATURE_{key.upper()}"
                    if os.getenv(env_var):
                        env_overrides.append((key, env_var, os.getenv(env_var)))
            
            if env_overrides:
                print(f"\n🔧 Environment Overrides:")
                for feature, env_var, value in env_overrides:
                    print(f"  {env_var} = {value}")
                    
        except Exception as e:
            print(f"❌ Failed to load feature flags: {e}")
    
    def check_production_readiness(self) -> bool:
        """Check if configuration is ready for production deployment"""
        print(f"🚀 Production Readiness Check")
        print(f"{'='*50}")
        
        checks = []
        
        # Environment validation
        print("1. Environment Validation...")
        env_valid = self.validate_environment('production', verbose=False)
        checks.append(('Environment Configuration', env_valid))
        
        # Feature flag validation
        print("\n2. Feature Flag Validation...")
        try:
            config = get_config()
            if hasattr(config, 'features'):
                features = config.features
                
                # Check production-critical features
                production_features = {
                    'structured_logging': True,
                    'security_headers': True,
                    'sql_injection_protection': True,
                    'pii_scrubbing': True,
                    'circuit_breaker': True
                }
                
                feature_issues = []
                for feature, expected in production_features.items():
                    if hasattr(features, feature):
                        actual = getattr(features, feature)
                        if actual != expected:
                            feature_issues.append(f"{feature} should be {expected} in production")
                
                features_valid = len(feature_issues) == 0
                if not features_valid:
                    print("❌ Feature flag issues:")
                    for issue in feature_issues:
                        print(f"  - {issue}")
                else:
                    print("✅ Feature flags configured for production")
                
                checks.append(('Feature Flags', features_valid))
            else:
                print("❌ Feature flags not configured")
                checks.append(('Feature Flags', False))
                
        except Exception as e:
            print(f"❌ Feature flag check failed: {e}")
            checks.append(('Feature Flags', False))
        
        # Security configuration
        print("\n3. Security Configuration...")
        security_checks = [
            ('LLM_API_KEY configured', bool(os.getenv('LLM_API_KEY'))),
            ('Database URL configured', bool(os.getenv('DATABASE_URL'))),
            ('Environment set to production', os.getenv('ENVIRONMENT', '').lower() == 'production'),
            ('Log level configured', bool(os.getenv('LOG_LEVEL')))
        ]
        
        security_valid = True
        for check_name, result in security_checks:
            status = "✅" if result else "❌"
            print(f"  {check_name}: {status}")
            if not result:
                security_valid = False
        
        checks.append(('Security Configuration', security_valid))
        
        # Overall result
        all_valid = all(result for _, result in checks)
        
        print(f"\n🎯 Overall Production Readiness: {'✅ READY' if all_valid else '❌ NOT READY'}")
        
        if not all_valid:
            print("\n🔧 Required Actions:")
            for check_name, result in checks:
                if not result:
                    print(f"  - Fix {check_name}")
        
        return all_valid
    
    def set_feature_flag(self, feature: str, value: bool) -> None:
        """Set a feature flag via environment variable"""
        env_var = f"FEATURE_{feature.upper()}"
        env_value = "true" if value else "false"
        
        print(f"🔧 Setting feature flag: {feature} = {value}")
        print(f"Environment variable: {env_var} = {env_value}")
        print(f"\nTo persist this setting, add to your environment:")
        print(f"export {env_var}={env_value}")
        
        # Set for current session
        os.environ[env_var] = env_value
        print("✅ Set for current session")
    
    def export_config(self, format: str = 'json') -> None:
        """Export current configuration"""
        try:
            config = get_config()
            
            if format == 'json':
                # Convert config to dict for JSON serialization
                config_dict = {
                    'database': config.database.__dict__,
                    'ui': config.ui.__dict__,
                    'security': config.security.__dict__,
                    'performance': config.performance.__dict__,
                    'ai': config.ai.__dict__,
                }
                
                if hasattr(config, 'features'):
                    config_dict['features'] = config.features.__dict__
                
                print(json.dumps(config_dict, indent=2))
            elif format == 'env':
                print("# Environment variables for current configuration")
                if hasattr(config, 'features'):
                    for key in dir(config.features):
                        if not key.startswith('_'):
                            value = getattr(config.features, key)
                            env_var = f"FEATURE_{key.upper()}"
                            env_value = "true" if value else "false"
                            print(f"export {env_var}={env_value}")
                            
        except Exception as e:
            print(f"❌ Failed to export configuration: {e}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Telecom Dashboard Configuration Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate environment configuration')
    validate_parser.add_argument('--environment', '-e', help='Target environment (production, staging, development)')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    
    # List features command
    list_parser = subparsers.add_parser('features', help='List feature flags')
    
    # Production readiness command
    prod_parser = subparsers.add_parser('production-check', help='Check production readiness')
    
    # Set feature flag command
    set_parser = subparsers.add_parser('set-feature', help='Set feature flag')
    set_parser.add_argument('feature', help='Feature flag name')
    set_parser.add_argument('value', choices=['true', 'false'], help='Feature flag value')
    
    # Export configuration command
    export_parser = subparsers.add_parser('export', help='Export configuration')
    export_parser.add_argument('--format', choices=['json', 'env'], default='json', help='Export format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ConfigManager()
    
    try:
        if args.command == 'validate':
            success = manager.validate_environment(args.environment, args.verbose)
            sys.exit(0 if success else 1)
            
        elif args.command == 'features':
            manager.list_feature_flags()
            
        elif args.command == 'production-check':
            ready = manager.check_production_readiness()
            sys.exit(0 if ready else 1)
            
        elif args.command == 'set-feature':
            value = args.value.lower() == 'true'
            manager.set_feature_flag(args.feature, value)
            
        elif args.command == 'export':
            manager.export_config(args.format)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
