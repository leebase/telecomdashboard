# Sprint 6 Evaluation Guide – Data Abstraction Layer

Use this checklist to validate Sprint 6 deliverables and ensure the view abstraction layer is properly implemented.

## Prerequisites
- Virtual environment with project dependencies installed
- Access to both SQLite (development) and Snowflake (production) databases
- Sprint 6 changes deployed to development environment
- Metadata pack updated to reference views

## 1. View Creation Validation

### SQLite View Creation
```bash
# Create views in SQLite
python scripts/create_views.py

# Verify views exist
sqlite3 data/telecom_db.sqlite ".tables" | grep "_view"
```
- ✅ Expected output includes views like: `dim_time_view`, `fact_network_metrics_view`, etc.
- ✅ No errors during view creation
- ✅ All required views created (7 dimension + 5 fact views)

### Snowflake View Creation
```bash
# Create views in Snowflake
python scripts/create_views.py --snowflake

# Verify views exist in Snowflake
# (Use Snowflake web interface or snowsql)
SHOW VIEWS IN SCHEMA analytics;
```
- ✅ All views created successfully in Snowflake
- ✅ No permission or syntax errors
- ✅ Views match SQLite structure

## 2. Metadata Integration Testing

### Metadata Validation
```bash
# Validate updated metadata pack
python -m metadata_cli validate metadata/dashboard_telco.yaml
```
- ✅ Validation passes without errors
- ✅ No references to direct table names
- ✅ All queries reference view names (e.g., `fact_network_metrics_view`)

### Metadata Content Check
```bash
# Check for view references in metadata
grep -n "_view" metadata/dashboard_telco.yaml
```
- ✅ All table references replaced with view names
- ✅ Consistent naming convention across all KPIs
- ✅ No remaining direct table references

## 3. Runtime Functionality Testing

### Application Startup
```bash
# Test with metadata runtime
USE_METADATA=true streamlit run app.py
```
- ✅ Application starts without errors
- ✅ All tabs load successfully
- ✅ KPI cards display data correctly
- ✅ Charts render with view-based data

### Query Execution Verification
```bash
# Check application logs for view usage
tail -f logs/telecom_dashboard.log | grep -i "select.*_view"
```
- ✅ All queries use view names
- ✅ No direct table queries in logs
- ✅ Query performance acceptable

## 4. Performance Benchmarking

### View vs Table Performance
```python
# Run performance comparison
python scripts/benchmark_views.py
```
- ✅ View queries within 10% of direct table performance
- ✅ No significant degradation in response times
- ✅ Memory usage remains acceptable

### Load Testing with Views
```bash
# Run load tests with view-based queries
python -m pytest tests/integration/test_view_performance.py -v
```
- ✅ Load tests pass with view queries
- ✅ Response times meet SLAs
- ✅ No memory leaks or performance degradation

## 5. Migration Strategy Validation

### Migration Script Testing
```bash
# Test migration script
python scripts/migrate_to_views.py --dry-run
python scripts/migrate_to_views.py --execute
```
- ✅ Dry run shows expected changes
- ✅ Migration executes without errors
- ✅ Rollback functionality works correctly

### Backward Compatibility
```bash
# Test legacy mode still works
USE_METADATA=false streamlit run app.py
```
- ✅ Legacy dashboard functions normally
- ✅ No interference with view implementation
- ✅ Feature flag works correctly

## 6. Integration Testing

### Cross-Database Compatibility
```python
# Test both databases with same metadata
python scripts/test_cross_db_compatibility.py
```
- ✅ SQLite and Snowflake produce identical results
- ✅ Schema differences handled gracefully
- ✅ Error handling works for both databases

### Client Data Integration Simulation
```bash
# Simulate client data structure
python scripts/simulate_client_data.py
```
- ✅ View layer adapts to different schemas
- ✅ Configuration changes work as expected
- ✅ Documentation covers customization process

## 7. Documentation and Maintenance

### Documentation Completeness
```bash
# Check documentation builds
mkdocs build docs/
```
- ✅ All documentation builds successfully
- ✅ View layer design documented
- ✅ Migration guide complete
- ✅ Client integration examples provided

### Maintenance Procedures
```bash
# Test view maintenance scripts
python scripts/maintain_views.py --check
python scripts/maintain_views.py --rebuild
```
- ✅ View health checks work
- ✅ Rebuild procedures function correctly
- ✅ Monitoring integration active

## Exit Criteria

Sprint 6 is successful when:
1. ✅ `python scripts/create_views.py` creates all required views in SQLite without errors
2. ✅ `python scripts/create_views.py --snowflake` creates equivalent views in Snowflake
3. ✅ `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes with view references
4. ✅ `USE_METADATA=true streamlit run app.py` renders correctly using view-based queries
5. ✅ Performance benchmarks show no significant degradation when using views vs direct tables
6. ✅ Migration scripts work correctly with rollback capability
7. ✅ All view-related tests pass with comprehensive coverage
8. ✅ Documentation covers view layer design, migration, and client integration

## Troubleshooting

### Common Issues and Solutions

#### View Creation Fails
```bash
# Check database permissions
# Verify table existence
sqlite3 data/telecom_db.sqlite ".tables"
```

#### Metadata Validation Errors
```bash
# Check for remaining table references
grep -n "fact_" metadata/dashboard_telco.yaml | grep -v "_view"
```

#### Performance Issues
```bash
# Enable query logging
export LOG_LEVEL=DEBUG
# Run performance profiler
python scripts/profile_queries.py
```

#### Migration Problems
```bash
# Check migration logs
tail -f logs/migration.log
# Use rollback if needed
python scripts/migrate_to_views.py --rollback
```

## Success Metrics

- **✅ 100% View Adoption**: Zero direct table queries in metadata runtime
- **✅ Performance Maintained**: <5% performance degradation with views
- **✅ Client Integration Ready**: Clean abstraction for different data schemas
- **✅ Comprehensive Testing**: >90% test coverage for view layer
- **✅ Documentation Complete**: Full coverage of design, migration, and maintenance

## Next Steps

After Sprint 6 completion:
1. **Client Onboarding**: Use view layer for first client data integration
2. **Advanced Features**: Consider materialized views for performance optimization
3. **Multi-Tenant**: Extend view layer for tenant isolation
4. **Monitoring**: Add view-specific health checks and metrics

The view abstraction layer provides a solid foundation for enterprise data integration while maintaining clean separation between application logic and physical data structures.