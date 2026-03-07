"""
Pytest configuration and shared fixtures for Telecom Dashboard tests
"""

import pytest
import sqlite3
import tempfile
import os
import sys
from unittest.mock import Mock, patch
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add src to path for importing modules
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database_connection import TelecomDatabase
from config_manager import ConfigManager, AppConfig
from llm_service import LLMService
from src.models.data_models import (
    KPIMetric, MetricValue, TrendData, BenchmarkData,
    NetworkMetrics, CustomerMetrics, QueryParameters
)
from src.exceptions.custom_exceptions import (
    DatabaseError, ConfigurationError, DataValidationError
)

# Test database fixtures
@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture(scope="session")
def test_database(test_db_path):
    """Create and populate test database"""
    # Create test database with schema
    conn = sqlite3.connect(test_db_path)
    
    # Create tables (simplified schema for testing)
    conn.executescript("""
        CREATE TABLE dim_region (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT NOT NULL,
            country TEXT,
            timezone TEXT
        );
        
        CREATE TABLE dim_time (
            time_id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            quarter INTEGER
        );
        
        CREATE TABLE fact_network_metrics (
            metric_id INTEGER PRIMARY KEY,
            time_id INTEGER,
            region_id INTEGER,
            availability REAL,
            latency REAL,
            packet_loss REAL,
            bandwidth_utilization REAL,
            mttr REAL,
            dropped_call_rate REAL,
            FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
            FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
        );
        
        CREATE TABLE fact_customer_experience (
            experience_id INTEGER PRIMARY KEY,
            time_id INTEGER,
            region_id INTEGER,
            satisfaction_score REAL,
            churn_rate REAL,
            nps REAL,
            first_contact_resolution REAL,
            avg_handling_time REAL,
            customer_lifetime_value REAL,
            FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
            FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
        );
    """)
    
    # Insert test data
    # Regions
    conn.execute("INSERT INTO dim_region VALUES (1, 'North', 'USA', 'EST')")
    conn.execute("INSERT INTO dim_region VALUES (2, 'South', 'USA', 'CST')")
    conn.execute("INSERT INTO dim_region VALUES (3, 'East', 'USA', 'EST')")
    conn.execute("INSERT INTO dim_region VALUES (4, 'West', 'USA', 'PST')")
    
    # Time data (last 30 days)
    base_date = datetime.now() - timedelta(days=30)
    for i in range(30):
        date = base_date + timedelta(days=i)
        conn.execute("""
            INSERT INTO dim_time (time_id, date, year, month, day, quarter) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (i+1, date.date().isoformat(), date.year, date.month, date.day, (date.month-1)//3 + 1))
    
    # Network metrics test data
    for time_id in range(1, 31):
        for region_id in range(1, 5):
            conn.execute("""
                INSERT INTO fact_network_metrics 
                (time_id, region_id, availability, latency, packet_loss, 
                 bandwidth_utilization, mttr, dropped_call_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time_id, region_id,
                99.5 + (time_id % 5) * 0.1,  # availability
                45.0 + (time_id % 3) * 2.0,   # latency
                0.1 + (time_id % 2) * 0.05,   # packet_loss
                65.0 + (time_id % 4) * 5.0,   # bandwidth_utilization
                2.5 + (time_id % 3) * 0.5,    # mttr
                0.2 + (time_id % 2) * 0.1     # dropped_call_rate
            ))
    
    # Customer experience test data
    for time_id in range(1, 31):
        for region_id in range(1, 5):
            conn.execute("""
                INSERT INTO fact_customer_experience
                (time_id, region_id, satisfaction_score, churn_rate, nps,
                 first_contact_resolution, avg_handling_time, customer_lifetime_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time_id, region_id,
                4.2 + (time_id % 3) * 0.2,    # satisfaction_score
                2.1 + (time_id % 2) * 0.3,    # churn_rate
                45.0 + (time_id % 4) * 5.0,   # nps
                85.0 + (time_id % 3) * 2.0,   # first_contact_resolution
                180.0 + (time_id % 2) * 30.0, # avg_handling_time
                1200.0 + (time_id % 5) * 100.0 # customer_lifetime_value
            ))
    
    conn.commit()
    conn.close()
    
    return test_db_path

@pytest.fixture
def telecom_db(test_database):
    """TelecomDatabase instance with test data"""
    return TelecomDatabase(test_database)

@pytest.fixture
def sample_network_metrics():
    """Sample network metrics data"""
    return {
        'availability': 99.9,
        'latency': 43.6,
        'packet_loss': 0.12,
        'bandwidth_utilization': 68.1,
        'mttr': 2.3,
        'dropped_call_rate': 0.21
    }

@pytest.fixture
def sample_customer_metrics():
    """Sample customer metrics data"""
    return {
        'satisfaction_score': 4.3,
        'churn_rate': 2.1,
        'nps': 52.0,
        'first_contact_resolution': 87.5,
        'avg_handling_time': 185.0,
        'customer_lifetime_value': 1350.0
    }

# Configuration fixtures
@pytest.fixture
def test_config():
    """Test configuration"""
    return AppConfig()

@pytest.fixture
def mock_config_manager():
    """Mock configuration manager"""
    with patch('config_manager.ConfigManager') as mock:
        config_instance = Mock()
        config_instance.config = AppConfig()
        mock.return_value = config_instance
        yield mock

# API fixtures
@pytest.fixture
def mock_llm_response():
    """Mock LLM API response"""
    return {
        'id': 'test-id',
        'choices': [{
            'message': {
                'content': '{"summary": "Test summary", "key_insights": ["Test insight"], "trends": ["Test trend"], "recommended_actions": ["Test action"]}'
            }
        }],
        'usage': {'total_tokens': 100}
    }

@pytest.fixture
def mock_requests():
    """Mock requests for API calls"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test-id',
            'choices': [{
                'message': {
                    'content': '{"summary": "Test summary", "key_insights": ["Test insight"], "trends": ["Test trend"], "recommended_actions": ["Test action"]}'
                }
            }]
        }
        mock_post.return_value = mock_response
        yield mock_post

@pytest.fixture
def llm_service():
    """Shared LLM service fixture for AI and security tests."""
    return LLMService()

# Data model fixtures
@pytest.fixture
def sample_kpi_metric():
    """Sample KPI metric model"""
    return KPIMetric(
        name="Network Availability",
        category="network",
        metric_type="percentage",
        current_value=MetricValue(value=99.9, unit="%"),
        previous_value=MetricValue(value=99.8, unit="%"),
        trend=TrendData(direction="up", strength=85.0, slope=0.1, period_days=30),
        benchmark=BenchmarkData(peer_average=99.5, industry_average=99.0),
        delta="+0.1%"
    )

@pytest.fixture
def sample_query_parameters():
    """Sample query parameters"""
    return QueryParameters(
        days=30,
        region="North",
        customer_segment="Enterprise"
    )

# Mock fixtures for external dependencies
@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components"""
    with patch.dict('sys.modules', {
        'streamlit': Mock(),
        'streamlit.components': Mock(),
        'streamlit.components.v1': Mock()
    }):
        yield

@pytest.fixture
def mock_pandas():
    """Mock pandas for testing without data"""
    with patch('pandas.read_sql_query') as mock_read_sql:
        mock_read_sql.return_value = pd.DataFrame({
            'availability': [99.9, 99.8, 99.7],
            'latency': [43.6, 44.1, 44.5],
            'packet_loss': [0.12, 0.11, 0.13]
        })
        yield mock_read_sql

# Security testing fixtures
@pytest.fixture
def mock_security_manager():
    """Mock security manager"""
    with patch('security_manager.security_manager') as mock_sm:
        mock_sm.validate_input.return_value = True
        mock_sm.rate_limit_check.return_value = True
        mock_sm.sanitize_output.return_value = "sanitized"
        yield mock_sm

# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Performance monitoring context manager"""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def __enter__(self):
            self.start_time = datetime.now()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = datetime.now()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return None
    
    return PerformanceMonitor()

# Parameterized test data
@pytest.fixture(params=[
    ("network", "availability", 99.9),
    ("network", "latency", 43.6),
    ("customer", "satisfaction", 4.3),
    ("customer", "churn_rate", 2.1)
])
def kpi_test_data(request):
    """Parameterized KPI test data"""
    category, metric, value = request.param
    return {
        'category': category,
        'metric': metric,
        'value': value
    }

# Error testing fixtures
@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing"""
    return {
        'database_error': DatabaseError("Test database error"),
        'config_error': ConfigurationError("Test config error"),
        'validation_error': DataValidationError("Test validation error")
    }

# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_environment():
    """Automatically cleanup environment after each test"""
    yield
    # Cleanup any temporary files, reset mocks, etc.
    # This runs after each test automatically

# Test data generators
def generate_time_series_data(days=30, base_value=100, variance=10):
    """Generate time series test data"""
    import random
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    values = [base_value + random.uniform(-variance, variance) for _ in range(days)]
    return list(zip(dates, values))

def generate_network_test_data(regions=4, days=30):
    """Generate comprehensive network test data"""
    data = []
    for region_id in range(1, regions + 1):
        for day in range(days):
            data.append({
                'region_id': region_id,
                'date': datetime.now() - timedelta(days=day),
                'availability': 99.0 + random.uniform(0, 1),
                'latency': 40.0 + random.uniform(0, 10),
                'packet_loss': random.uniform(0, 0.5)
            })
    return data

# Test utilities
class TestHelpers:
    """Helper methods for testing"""
    
    @staticmethod
    def assert_kpi_structure(kpi_data):
        """Assert that KPI data has expected structure"""
        required_fields = ['name', 'category', 'current_value']
        for field in required_fields:
            assert field in kpi_data, f"Missing required field: {field}"
    
    @staticmethod
    def assert_response_time_under(func, max_seconds=1.0):
        """Assert that function executes within time limit"""
        start = datetime.now()
        result = func()
        duration = (datetime.now() - start).total_seconds()
        assert duration < max_seconds, f"Function took {duration}s, max allowed: {max_seconds}s"
        return result
    
    @staticmethod
    def create_mock_dataframe(rows=10, columns=None):
        """Create mock DataFrame for testing"""
        if columns is None:
            columns = ['value', 'timestamp', 'region']
        
        data = {}
        for col in columns:
            if col == 'timestamp':
                data[col] = [datetime.now() - timedelta(days=i) for i in range(rows)]
            elif col == 'region':
                data[col] = [f'Region_{i%4}' for i in range(rows)]
            else:
                data[col] = [random.uniform(0, 100) for _ in range(rows)]
        
        return pd.DataFrame(data)

@pytest.fixture
def test_helpers():
    """Test helper methods"""
    return TestHelpers()
