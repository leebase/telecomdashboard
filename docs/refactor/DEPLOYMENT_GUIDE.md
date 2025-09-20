# Deployment Guide – Metadata Runtime

## Prerequisites

### System Requirements
- Python 3.8+
- SQLite 3.24+ (for local development)
- Snowflake account (for production)
- 4GB RAM minimum, 8GB recommended
- 10GB disk space

### Dependencies
```bash
pip install -r requirements.txt
pip install snowflake-connector-python  # For Snowflake support
```

## Environment Setup

### 1. Create Environment File
```bash
cp config.template.yaml config.secrets.yaml
```

### 2. Configure Environment Variables
```bash
# Database Configuration
export DATABASE_PATH="data/telecom_db.sqlite"

# Snowflake Configuration (Production)
export SNOWFLAKE_DSN="user=your_user;password=your_password;account=your_account;warehouse=your_warehouse;database=your_database;schema=your_schema"

# Application Settings
export USE_METADATA=true
export LOG_LEVEL=INFO
export SESSION_TIMEOUT=3600

# Security
export JWT_SECRET_KEY="your-256-bit-secret"
```

### 3. Initialize Database
```bash
# For SQLite development
python load_csv_data.py

# For Snowflake production
# Data should be pre-loaded in Snowflake warehouse
```

## Deployment Options

### Option 1: Local Development
```bash
# Start the application
streamlit run app.py

# Or run metadata-only mode
USE_METADATA=true streamlit run app.py
```

### Option 2: Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run
docker build -t telecom-dashboard .
docker run -p 8501:8501 -e USE_METADATA=true telecom-dashboard
```

### Option 3: Production Server
```bash
# Using Gunicorn for production
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:8000 app:server
```

## Configuration Management

### Metadata Configuration
- Place `metadata/dashboard_telco.yaml` in the metadata directory
- Validate configuration: `python -m metadata_cli validate metadata/dashboard_telco.yaml`
- For multi-environment: Use different metadata packs per environment

### Feature Flags
```python
# In production, enable enterprise features
USE_METADATA=true
ENABLE_AUDIT_LOGGING=true
ENABLE_HEALTH_CHECKS=true
ENABLE_LOAD_TESTING=false
```

## Monitoring Setup

### Health Checks
```bash
# Simple health check
curl http://localhost:8501/?health=simple

# Detailed health check
curl http://localhost:8501/?health=detailed

# Feature flags status
curl http://localhost:8501/?health=features
```

### Logging Configuration
```python
# In config/logging_config.py
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/telecom_dashboard.log"
AUDIT_LOG_FILE = "logs/audit.log"
```

### Metrics Collection
```python
# Enable metrics collection
from src.monitoring.health_monitor import metrics_collector, health_checker

# Start monitoring
health_checker.start_monitoring()

# Collect metrics
metrics = metrics_collector.collect_system_metrics()
```

## Security Configuration

### Authentication Setup
```python
# Configure users in config/users.json
{
  "users": [
    {
      "user_id": "admin",
      "username": "admin",
      "email": "admin@company.com",
      "roles": ["admin"],
      "groups": ["administrators"],
      "is_active": true
    }
  ]
}
```

### Authorization Configuration
```yaml
# In metadata pack security section
security:
  roles:
    analyst:
      permissions:
        - resource: "dashboard"
          action: "view"
        - resource: "reports"
          action: "read"
  role_hierarchy:
    admin: ["analyst", "manager"]
```

## Performance Tuning

### Database Optimization
```python
# Connection pooling settings
SNOWFLAKE_MAX_CONNECTIONS = 10
SNOWFLAKE_CONNECTION_TIMEOUT = 30

# Query optimization
QUERY_TIMEOUT = 300  # 5 minutes
CACHE_TTL = 300      # 5 minutes
```

### Caching Configuration
```python
# Enable caching for better performance
ENABLE_QUERY_CACHE = true
CACHE_MAX_SIZE = 100
CACHE_TTL_SECONDS = 300
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check database file permissions
ls -la data/telecom_db.sqlite

# For Snowflake
# Verify DSN configuration
echo $SNOWFLAKE_DSN

# Test connection
python -c "import snowflake.connector; conn = snowflake.connector.connect(os.getenv('SNOWFLAKE_DSN')); print('Connected')"
```

#### 2. Metadata Validation Errors
```bash
# Validate metadata pack
python -m metadata_cli validate metadata/dashboard_telco.yaml --verbose

# Check for missing required fields
python -m metadata_cli validate metadata/dashboard_telco.yaml --json | jq .
```

#### 3. Performance Issues
```bash
# Check system metrics
python -c "from src.monitoring.health_monitor import metrics_collector; print(metrics_collector.collect_system_metrics())"

# Analyze slow queries
python -c "from src.data.async_executor import query_optimizer; print(query_optimizer.identify_slow_queries())"
```

#### 4. Authentication Problems
```bash
# Check user configuration
cat config/users.json

# Verify JWT secret
echo $JWT_SECRET_KEY

# Test authentication
python -c "from src.security.auth_manager import init_auth_system; auth, session, rbac = init_auth_system(config); print('Auth system initialized')"
```

### Log Analysis
```bash
# View application logs
tail -f logs/telecom_dashboard.log

# View audit logs
tail -f logs/audit.log

# Search for errors
grep "ERROR" logs/telecom_dashboard.log
```

## Backup and Recovery

### Database Backup
```bash
# SQLite backup
cp data/telecom_db.sqlite data/telecom_db_backup.sqlite

# Snowflake backup (handled by Snowflake)
# Use Snowflake's Time Travel feature
```

### Configuration Backup
```bash
# Backup metadata and configuration
tar -czf backup_$(date +%Y%m%d).tar.gz metadata/ config/ logs/
```

### Recovery Procedures
```bash
# Restore from backup
tar -xzf backup_20241201.tar.gz

# Validate restored configuration
python -m metadata_cli validate metadata/dashboard_telco.yaml

# Restart application
streamlit run app.py
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple instances
- Configure session affinity for Streamlit
- Use shared cache (Redis) for multi-instance deployments

### Vertical Scaling
- Increase server resources for larger datasets
- Optimize database queries and indexing
- Implement query result pagination

### Monitoring at Scale
- Set up centralized logging (ELK stack)
- Configure alerting for key metrics
- Implement auto-scaling based on load

## Support and Maintenance

### Regular Maintenance Tasks
```bash
# Daily
# Check health status
curl http://localhost:8501/?health=detailed

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete

# Weekly
# Update dependencies
pip install --upgrade -r requirements.txt

# Analyze performance
python -c "from src.monitoring.health_monitor import metrics_collector; print(metrics_collector.get_average_metrics(168))"

# Monthly
# Review audit logs
python -c "from src.security.audit_logger import get_audit_logger; logger = get_audit_logger(); print(logger.get_events_summary(720))"
```

### Getting Help
- Check application logs for error details
- Review health check endpoints for system status
- Use audit logs to trace user actions and system events
- Consult the troubleshooting section above for common issues

This deployment guide provides a comprehensive foundation for running the metadata runtime in development and production environments.