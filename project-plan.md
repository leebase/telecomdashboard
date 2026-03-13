# telecom-metadata Project Plan

> Medium-term roadmap for turning the current runtime slice into a credible
> metadata-driven dashboard reproduction engine.

---

## Phase 1: Boot And Validation Repair

### Goal

Restore a working metadata runtime in the supported local environment.

### Priority Outcomes

- Fix the Pydantic/runtime mismatch
- Make metadata CLI validation work
- Make the canonical telco pack load
- Get the metadata test buckets running again

### Exit Gate

- `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
- Metadata-focused tests run without import-time failure
- Metadata mode starts through the main app path

---

## Phase 2: Full Telco Parity

### Goal

Reproduce the source telecom dashboard’s shell, repeated page pattern, and
special benchmark page from metadata.

### Priority Outcomes

- Model the shell explicitly in metadata/runtime
- Eliminate placeholder widget fallbacks for required telco surfaces
- Match the tab/page contract defined by the source screen spec
- Make metadata mode feel like the same product, not a debug shell

### Exit Gate

- Metadata mode renders the intended headers, controls, tabs, KPI regions,
  charts, detail sections, and benchmark surfaces
- Remaining differences are known, intentional, and documented

---

## Phase 3: Proof Harness Hardening

### Goal

Make the parity claim testable and difficult to fake.

### Priority Outcomes

- Add structural parity assertions
- Add data-parity comparison between legacy and metadata paths
- Replace mocked visual parity with real browser screenshot checks
- Make proof runnable from one repeatable command path

### Exit Gate

- Structural, data, and browser proof checks all pass
- Failures are actionable and reflect real regressions
- The repo can make a narrow, defensible telco-parity claim

---

## Phase 4: Generalization Beyond Telco

### Goal

Generalize only the abstractions that survived the telco proof.

### Priority Outcomes

- Separate telco-specific assumptions from runtime-owned abstractions
- Decide what metadata concepts are truly cross-domain
- Introduce a second proof pack only after telco parity is stable

### Exit Gate

- A second domain can be modeled without weakening telco proof quality
- The repo can justify broader positioning with real evidence

---

## Decision Gates

The project should not claim:

- “any dashboard”
- “general-purpose metadata runtime”
- “verified parity”

until all of the following are true:

1. Telco pack validates and loads
2. Metadata mode reproduces the target shell and widget surface
3. Structural parity checks pass
4. Data parity checks pass
5. Browser-level visual proof passes

Until those gates are met, the correct positioning is narrower: this repo is a
promising but unfinished metadata-proof implementation focused on the telecom dashboard.
