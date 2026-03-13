# telecom-metadata Architecture

> Current architecture summary for the metadata-proof codebase.

---

## Primary Runtime

The main proof path is the existing Streamlit application launched with:

```bash
USE_METADATA=true streamlit run app.py
```

`app.py` still contains the legacy telecom dashboard, but can switch into the
metadata runtime via `ui.runtime_switch.is_metadata_enabled()`.

---

## Major Components

### Legacy And Entry-Point Layer

- `app.py`: legacy dashboard runtime plus metadata feature-flag branch
- `apps/meta/app.py`: metadata-only entry point for isolated runtime testing
- `src/ui/runtime_switch.py`: `USE_METADATA` flag helper

### Metadata Runtime Core

- `src/metadata_runtime/models.py`: metadata schema models
- `src/metadata_runtime/loader.py`: YAML loading, validation, and cache
- `src/metadata_runtime/dialects/`: macro registry and dialect support
- `src/metadata_runtime/cli.py`: metadata validation CLI

### Data And Execution

- `src/data/query_compiler.py`: Jinja-based SQL rendering from metadata and filters
- `src/data/datasource.py`: datasource abstraction and factory
- `src/data/metadata_provider.py`: KPI/chart payload assembly for metadata widgets
- `src/data/cache.py`: runtime caching helpers

### UI And Rendering

- `src/ui/metadata_runtime_app.py`: top-level metadata dashboard renderer
- `src/ui/layout_engine.py`: metadata layout execution
- `src/ui/metadata_widgets.py`: widget registry and renderer dispatch
- `src/ui/visual_parity.py`: current parity-oriented utility layer

### Metadata Assets And Support Tooling

- `metadata/dashboard_telco.yaml`: canonical telco proof pack
- `tools/generate_telco_metadata.py`: deterministic telco pack normalization
  tool with stable provenance metadata
- `scripts/create_views.py`: database-view support used by metadata/query tests

### Tests

- `tests/metadata/`: schema, loader, dialect, and CLI tests
- `tests/data/`: datasource, compiler, provider, and query/view validation tests
- `tests/ui/`: layout, runtime switch, widget, and parity utility tests
- `tests/visual/`: visual parity tests, currently skeletal

---

## Runtime Flow

1. `app.py` or `apps/meta/app.py` enters metadata mode.
2. `src/metadata_runtime/loader.py` loads and validates the YAML pack.
3. `src/data/query_compiler.py` renders SQL for metadata-defined metrics.
4. `src/data/datasource.py` executes queries against configured sources.
5. `src/data/metadata_provider.py` converts query results into widget payloads.
6. `src/ui/layout_engine.py` walks the metadata layout and dispatches widgets.
7. `src/ui/metadata_widgets.py` renders supported widget types into Streamlit.

---

## Architectural Drift

- `src/metadata_runtime/models.py` uses Pydantic v2 APIs such as
  `model_validator`, while `requirements.txt` pins `pydantic<2`
- Visual parity code is still mocked and does not perform real screenshot diffs
- `tools/generate_telco_metadata.py` now produces a deterministic normalized
  snapshot of the canonical pack, but it still does not perform true legacy
  introspection
- `src/ui/metadata_runtime_app.py` does not yet reproduce the full source
  dashboard shell or all required widget surfaces
- Widget-slot resolution is incomplete; unsupported widget slots currently fall
  back to placeholders

---

## Dependency Source Policy

- `requirements.txt` and `requirements-security.txt` are the current install sources
- Runtime and dependency declarations are not yet fully aligned
- Proof claims should be based on what runs in the pinned environment, not on
  what the design docs intend

---

## Working Assumption For Future Sessions

Unless the task explicitly targets the legacy dashboard path as a comparison
surface, optimize for the metadata runtime and treat the legacy UI as the proof target.
