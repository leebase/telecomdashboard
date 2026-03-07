"""
Unit tests for config_manager module
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from config_manager import (
    ConfigManager, AppConfig, DatabaseConfig, UIConfig, 
    SecurityConfig, PerformanceConfig, AIConfig,
    get_config, get_database_config
)
from src.exceptions.custom_exceptions import ConfigurationError


@pytest.fixture
def isolated_config_manager(tmp_path):
    """Provide a config manager that cannot mutate the repo config."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    manager = ConfigManager()
    manager.config_dir = config_dir
    return manager


class TestDatabaseConfig:
    """Test DatabaseConfig model"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = DatabaseConfig()
        assert config.path == "data/telecom_db.sqlite"
        assert config.connection_timeout == 30000
        assert config.enable_foreign_keys is True
        assert config.cache_size == 32
        assert config.trend_cache_size == 16
    
    def test_custom_values(self):
        """Test custom configuration values"""
        config = DatabaseConfig(
            path="custom/path.db",
            connection_timeout=60000,
            cache_size=64
        )
        assert config.path == "custom/path.db"
        assert config.connection_timeout == 60000
        assert config.cache_size == 64
    
    def test_path_validation(self):
        """Test database path validation"""
        # Valid paths
        valid_paths = ["data/test.sqlite", "db/app.db", "/abs/path.sqlite"]
        for path in valid_paths:
            config = DatabaseConfig(path=path)
            assert config.path == path
        
        # Invalid paths
        with pytest.raises(ValueError, match="Database path must end with"):
            DatabaseConfig(path="invalid.txt")

class TestUIConfig:
    """Test UIConfig model"""
    
    def test_default_values(self):
        """Test default UI configuration"""
        config = UIConfig()
        assert config.default_theme == "verizon"
        assert config.page_title == "Telecom KPI Dashboard"
        assert config.page_icon == "📡"
        assert config.layout == "wide"
        assert config.sidebar_state == "expanded"
        assert config.show_debug_info is False
    
    def test_layout_validation(self):
        """Test layout validation"""
        # Valid layouts
        for layout in ["wide", "centered"]:
            config = UIConfig(layout=layout)
            assert config.layout == layout
        
        # Invalid layout
        with pytest.raises(ValueError, match="Layout must be either"):
            UIConfig(layout="invalid")
    
    def test_sidebar_state_validation(self):
        """Test sidebar state validation"""
        # Valid states
        for state in ["expanded", "collapsed", "auto"]:
            config = UIConfig(sidebar_state=state)
            assert config.sidebar_state == state
        
        # Invalid state
        with pytest.raises(ValueError, match="Sidebar state must be"):
            UIConfig(sidebar_state="invalid")

class TestSecurityConfig:
    """Test SecurityConfig model"""
    
    def test_default_values(self):
        """Test default security configuration"""
        config = SecurityConfig()
        assert config.enable_rate_limiting is True
        assert config.max_requests_per_minute == 60
        assert config.enable_input_validation is True
        assert config.enable_output_sanitization is True
        assert config.enable_security_logging is True
        assert config.log_file == "security.log"
    
    def test_rate_limit_validation(self):
        """Test rate limit validation"""
        # Valid values
        config = SecurityConfig(max_requests_per_minute=100)
        assert config.max_requests_per_minute == 100
        
        # Invalid values
        with pytest.raises(ValueError):
            SecurityConfig(max_requests_per_minute=0)
        
        with pytest.raises(ValueError):
            SecurityConfig(max_requests_per_minute=1001)

class TestAIConfig:
    """Test AIConfig model"""
    
    def test_default_values(self):
        """Test default AI configuration"""
        config = AIConfig()
        assert config.model == "google/gemini-2.5-flash"
        assert config.temperature == 0.1
        assert config.max_tokens == 2000
        assert config.api_timeout == 30
        assert config.enable_insights is True
    
    def test_temperature_validation(self):
        """Test temperature validation"""
        # Valid temperatures
        for temp in [0.0, 0.5, 1.0, 2.0]:
            config = AIConfig(temperature=temp)
            assert config.temperature == temp
        
        # Invalid temperatures
        with pytest.raises(ValueError):
            AIConfig(temperature=-0.1)
        
        with pytest.raises(ValueError):
            AIConfig(temperature=2.1)
    
    def test_token_validation(self):
        """Test token count validation"""
        # Valid token counts
        config = AIConfig(max_tokens=1000)
        assert config.max_tokens == 1000
        
        # Invalid token counts
        with pytest.raises(ValueError):
            AIConfig(max_tokens=50)  # Too low
        
        with pytest.raises(ValueError):
            AIConfig(max_tokens=15000)  # Too high

class TestAppConfig:
    """Test main AppConfig model"""
    
    def test_default_initialization(self):
        """Test default app configuration"""
        config = AppConfig()
        
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.ui, UIConfig)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.ai, AIConfig)
    
    def test_validation_on_init(self):
        """Test that validation runs on initialization"""
        # Valid config
        config = AppConfig()
        assert config is not None
        
        # Test validation method exists and runs
        config._validate_config()  # Should not raise
    
    def test_invalid_config_validation(self):
        """Test validation catches invalid configurations"""
        config = AppConfig()
        
        # Test invalid database cache size
        config.database.cache_size = 0
        with pytest.raises(ValueError, match="Database cache size must be at least 1"):
            config._validate_config()
        
        # Test invalid performance cache TTL
        config = AppConfig()
        config.performance.cache_ttl_seconds = -1
        with pytest.raises(ValueError, match="Cache TTL cannot be negative"):
            config._validate_config()

class TestConfigManager:
    """Test ConfigManager class"""
    
    def test_initialization(self):
        """Test ConfigManager initialization"""
        manager = ConfigManager()
        assert manager.config_file == "config.yaml"
        assert manager.config_dir == Path("config")
        assert manager._config is None
    
    def test_custom_config_file(self):
        """Test ConfigManager with custom config file"""
        manager = ConfigManager("custom.yaml")
        assert manager.config_file == "custom.yaml"
    
    @patch('pathlib.Path.exists')
    def test_load_config_no_file(self, mock_exists):
        """Test loading config when file doesn't exist"""
        mock_exists.return_value = False
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert isinstance(config, AppConfig)
        # Should return default config
        assert config.database.path == "data/telecom_db.sqlite"
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config_from_file(self, mock_yaml_load, mock_file, mock_exists):
        """Test loading config from existing file"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            'database': {
                'path': 'custom/db.sqlite',
                'cache_size': 64
            },
            'ui': {
                'page_title': 'Custom Dashboard'
            }
        }
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.database.path == 'custom/db.sqlite'
        assert config.database.cache_size == 64
        assert config.ui.page_title == 'Custom Dashboard'
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_config_yaml_error(self, mock_yaml_load, mock_file, mock_exists):
        """Test handling of YAML parsing errors"""
        mock_exists.return_value = True
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
        
        with patch('config_manager.logger') as mock_logger:
            manager = ConfigManager()
            config = manager.load_config()
            
            # Should return default config and log warning
            assert isinstance(config, AppConfig)
            mock_logger.warning.assert_called()
    
    def test_save_config(self):
        """Test saving configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()
            
            manager = ConfigManager()
            manager.config_dir = config_dir
            
            config = AppConfig()
            config.database.path = "test/db.sqlite"
            
            manager.save_config(config)
            
            # Check file was created
            config_file = config_dir / "config.yaml"
            assert config_file.exists()
            
            # Check content
            with open(config_file) as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data['database']['path'] == "test/db.sqlite"
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_config_error(self, mock_file):
        """Test handling of save errors"""
        manager = ConfigManager()
        config = AppConfig()
        
        with patch('config_manager.logger') as mock_logger:
            manager.save_config(config)
            mock_logger.error.assert_called()
    
    def test_get_config_lazy_loading(self, isolated_config_manager):
        """Test lazy loading of configuration"""
        manager = isolated_config_manager
        assert manager._config is None
        
        # First access should load config
        config1 = manager.config
        assert manager._config is not None
        assert isinstance(config1, AppConfig)
        
        # Second access should return cached config
        config2 = manager.config
        assert config1 is config2
    
    def test_get_specific_configs(self, isolated_config_manager):
        """Test getting specific configuration sections"""
        manager = isolated_config_manager
        
        db_config = manager.get_database_config()
        assert isinstance(db_config, DatabaseConfig)
        
        ui_config = manager.get_ui_config()
        assert isinstance(ui_config, UIConfig)
        
        security_config = manager.get_security_config()
        assert isinstance(security_config, SecurityConfig)
        
        perf_config = manager.get_performance_config()
        assert isinstance(perf_config, PerformanceConfig)
        
        ai_config = manager.get_ai_config()
        assert isinstance(ai_config, AIConfig)
    
    def test_update_config(self, isolated_config_manager):
        """Test updating configuration"""
        manager = isolated_config_manager
        
        # Update database config
        manager.update_config(
            database={'path': 'new/path.sqlite', 'cache_size': 128},
            ui={'page_title': 'Updated Dashboard'}
        )
        
        config = manager.config
        assert config.database.path == 'new/path.sqlite'
        assert config.database.cache_size == 128
        assert config.ui.page_title == 'Updated Dashboard'
    
    def test_update_config_invalid_section(self, isolated_config_manager):
        """Test updating with invalid configuration section"""
        manager = isolated_config_manager
        
        with patch('config_manager.logger') as mock_logger:
            manager.update_config(invalid_section={'key': 'value'})
            mock_logger.warning.assert_called_with("Unknown config section: invalid_section")
    
    def test_update_config_invalid_key(self, isolated_config_manager):
        """Test updating with invalid configuration key"""
        manager = isolated_config_manager
        
        with patch('config_manager.logger') as mock_logger:
            manager.update_config(database={'invalid_key': 'value'})
            mock_logger.warning.assert_called_with("Unknown config key: database.invalid_key")
    
    def test_reset_to_defaults(self, isolated_config_manager):
        """Test resetting configuration to defaults"""
        manager = isolated_config_manager
        
        # Modify config
        manager.update_config(database={'path': 'custom.sqlite'})
        assert manager.config.database.path == 'custom.sqlite'
        
        # Reset to defaults
        with patch.object(manager, 'save_config') as mock_save:
            manager.reset_to_defaults()
            
            # Config should be reset
            assert manager.config.database.path == "data/telecom_db.sqlite"
            mock_save.assert_called_once()

class TestGlobalConfigFunctions:
    """Test global configuration functions"""
    
    @patch('config_manager.config_manager')
    def test_get_config(self, mock_manager):
        """Test global get_config function"""
        mock_config = Mock()
        mock_manager.config = mock_config
        
        result = get_config()
        assert result is mock_config
    
    @patch('config_manager.config_manager')
    def test_get_database_config(self, mock_manager):
        """Test global get_database_config function"""
        mock_db_config = Mock()
        mock_manager.get_database_config.return_value = mock_db_config
        
        result = get_database_config()
        assert result is mock_db_config
        mock_manager.get_database_config.assert_called_once()

class TestConfigValidation:
    """Test configuration validation edge cases"""
    
    def test_nested_config_validation(self):
        """Test validation of nested configuration objects"""
        config = AppConfig()
        
        # Test that nested objects are properly validated
        assert hasattr(config.database, 'path')
        assert hasattr(config.ui, 'page_title')
        assert hasattr(config.security, 'enable_rate_limiting')
    
    def test_config_serialization(self, isolated_config_manager):
        """Test configuration serialization to dict"""
        manager = isolated_config_manager
        config = AppConfig()
        
        config_dict = manager._config_to_dict(config)
        
        assert 'database' in config_dict
        assert 'ui' in config_dict
        assert 'security' in config_dict
        assert 'performance' in config_dict
        assert 'ai' in config_dict
        
        # Check nested structure
        assert 'path' in config_dict['database']
        assert 'page_title' in config_dict['ui']
    
    def test_config_deserialization(self, isolated_config_manager):
        """Test configuration deserialization from dict"""
        manager = isolated_config_manager
        config_data = {
            'database': {'path': 'test.sqlite', 'cache_size': 64},
            'ui': {'page_title': 'Test Dashboard'},
            'security': {'max_requests_per_minute': 120}
        }
        
        config = manager._create_config_from_dict(config_data)
        
        assert config.database.path == 'test.sqlite'
        assert config.database.cache_size == 64
        assert config.ui.page_title == 'Test Dashboard'
        assert config.security.max_requests_per_minute == 120

