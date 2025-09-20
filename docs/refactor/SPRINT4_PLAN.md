# Sprint 4 Plan – Metadata Runtime

## Sprint Goal
Ship a production-ready metadata runtime slice that caches KPI results, auto-generates the telco pack, and proves UI parity end-to-end. Prioritize SQLite for development to reach "product accepted" mode, with multi-database options baked in for future Snowflake integration.

## Scope & Deliverables
- **C3 – Caching Policy & Invalidation**
  - Implement TTL-aware cache module wired into `MetadataDataProvider` and expose CLI hooks for cache inspection/clear.
  - Focus on SQLite-compatible caching with optional materialized views.
  - Unit tests (`tests/data/test_cache.py`) covering hit/miss, invalidation, and TTL expiration.
- **D1 – Auto-Generate Telco Metadata**
  - Deliver `tools/generate_telco_metadata.py` that produces the pack consumed by the runtime, with diff review automation.
  - Ensure generated pack aligns with SQLite views and supports all KPIs.
  - Tests (`tests/tools/test_generate_telco_metadata.py`) comparing output to fixtures.
- **D3 – Visual Parity Verification**
  - Add screenshot/DOM diff harness covering all subject areas using the metadata runtime.
  - Baseline assets under `tests/visual/baseline/` for comparison.
  - Tests (`tests/visual/test_visual_parity.py -m visual`) with tolerance ≤2%.
- **E2 – Developer Playbook & Examples**
  - Publish example packs (`examples/retail_pack.yaml`, `examples/healthcare_pack.yaml`) plus contributor guidance.
  - Update `docs/CONTRIBUTING.md` with PR process, test expectations, review checklist.
  - Validation tests for example packs.
- **SQLite Integration Focus**
  - Ensure all components (datasource, query compiler, cache) work seamlessly with SQLite.
  - Add integration tests for end-to-end metadata runtime with SQLite data.
  - Document SQLite-specific setup and limitations for development.

## Definition of Done
- `pytest tests/data/test_cache.py -q` passes, confirming cache behavior.
- `python tools/generate_telco_metadata.py --output metadata/dashboard_telco.yaml --validate` completes with zero diffs.
- `pytest tests/visual/test_visual_parity.py -m visual` produces green diffs for all subject areas.
- `python -m metadata_cli validate metadata/dashboard_telco.yaml` validates regenerated pack.
- `USE_METADATA=true streamlit run app.py` smoke run confirms functionality with SQLite.
- Docs/examples build successfully.

## Out of Scope
- Full Snowflake production deployment.
- Advanced theming or responsive design beyond current scope.
- Real-time data streaming or AI insights integration.

## Risks & Mitigations
- **Caching Complexity** → Start with simple in-memory cache, expand to SQLite-backed if needed.
- **Pack Generation Accuracy** → Manual review of generated YAML before commit.
- **Visual Test Brittleness** → Use headless browser with stable baselines.

## Sprint Review Checklist
1. Demo caching behavior and auto-generated pack.
2. Review visual parity test results.
3. Walk through example packs and updated docs.
4. Capture feedback for Sprint 5 (e.g., Snowflake integration, advanced features).