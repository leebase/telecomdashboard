# telecom-metadata Product Definition

> Concise product definition for the metadata-proof phase.

---

## Product Summary

`telecom-metadata` is a metadata-driven dashboard runtime intended to recreate
the existing telecom KPI dashboard first, then generalize that runtime for
other dashboard domains only after parity is proven.

---

## Primary Users

- Developers building and validating the metadata runtime
- Teams proving that a concrete Streamlit dashboard can be recreated from metadata
- Stakeholders evaluating whether the runtime is credible enough to generalize

---

## Core User Jobs

- Define dashboard structure, widgets, and data bindings in metadata
- Render a concrete dashboard experience from a metadata pack
- Verify that metadata-driven output matches the source dashboard structurally,
  numerically, and visually
- Decide when the runtime is strong enough to support non-telco packs

---

## Current Product Scope

### In Scope

- Metadata runtime in `src/metadata_runtime/`, `src/ui/`, and `src/data/`
- Telco proof pack in `metadata/dashboard_telco.yaml`
- Metadata-mode rendering through `USE_METADATA=true streamlit run app.py`
- Metadata-only runtime entry point in `apps/meta/app.py`
- Validation and parity tooling for the telco proof

### Explicit First Proof Domain

- The telecom dashboard inherited in this repo from the source dashboard project

### Not Yet Confirmed As Product Reality

- Broad “any dashboard” support
- Fully automated pack generation from arbitrary legacy dashboards
- A verified proof harness strong enough to certify parity today

---

## Success Criteria For This Phase

- The canonical telco pack validates and loads
- Metadata mode recreates the telco dashboard shell and core behavior
- KPI and chart outputs can be compared automatically against the legacy path
- Browser-level verification confirms the rendered experience is materially equivalent
- The repo can defend a narrow claim: telco reproduction via metadata is proven

---

## Non-Goals For This Phase

- Marketing broad multi-industry support before proof exists
- Rebuilding the source dashboard for its own sake
- Treating YAML-driven tab stubs as sufficient evidence of reproduction

---

Use this document to keep the repo anchored on telco proof before generalization.
