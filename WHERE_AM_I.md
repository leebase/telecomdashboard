# WHERE_AM_I — telecom-metadata

> Product-level orientation. For session detail, read `context.md`.

---

## Project Health

| Attribute | Value |
|-----------|-------|
| Project | telecom-metadata |
| Current Phase | Telco Parity Proof Sprint |
| Overall Status | 🟡 The local telco proof gate is now green through the metadata entry path, but architecture cleanup and generator hardening remain before broader claims; the separate `connie-book/` workspace is now wired to a live Linear-backed Symphony runtime, and its false-close path is now guarded while the first clean artifact-producing run is still underway |
| Last Updated | 2026-03-12 |

---

## Progress Against Product Goals

### Product Goals

| Goal | Status | Notes |
|------|--------|-------|
| Reproduce the source telecom dashboard from metadata | ✅ Local proof achieved | The proof gate is green in the local metadata entry path, including benchmark management |
| Validate a metadata schema and pack for the telco proof domain | ✅ Locally restored | Canonical pack now validates and the maintained metadata/data/ui suites are green |
| Render dashboard structure from metadata instead of bespoke page code | 🟡 Mostly implemented | Tab/layout/KPI plumbing exists, metadata mode shares the legacy shell, and pack-defined chart/widget overrides resolve across all six telco tabs |
| Verify parity structurally, by data output, and visually | ✅ Local proof gate met | Structural/data/browser proof now all pass in the local pinned environment |
| Generalize beyond telco after proof | ⏸️ Not started | No broader claim should be made until telco parity is verifiably green |

### Current Sprint Goals

| Goal | Status | Notes |
|------|--------|-------|
| Re-baseline AgentFlow docs to the metadata repo | ✅ Done | Core memory and project-definition docs now exist |
| Restore metadata boot and validation | ✅ Done for local proof baseline | Metadata validation passes, maintained metadata/data/ui suites are green, and metadata mode starts headlessly |
| Close UI/runtime gaps against the source dashboard contract | ✅ Done for the local proof baseline | Browser-visible parity is green locally and benchmark management now renders through metadata-owned widgets |
| Build a trustworthy proof harness | ✅ Done for the local proof baseline | Maintained structural/data proof is green and browser-real screenshot checks now pass |

---

## Sprint Position

| Sprint | Focus | Status |
|--------|-------|--------|
| Telco Parity Proof Sprint | Runtime repair, shell parity, proof automation | ✅ Local proof gate met |

---

## Product Risks and Blockers

| Risk or Blocker | Impact | Status |
|-----------------|--------|--------|
| Legacy/dashboard coupling remains visible in shell styling | The runtime still reuses legacy shell primitives even though the benchmark surface is now metadata-owned | 🟡 Active |
| “Any dashboard” positioning is ahead of the evidence | Overclaim risk is high until telco parity is actually demonstrated | 🟡 Active |
| Pack generation is only partially hardened | The generator is now deterministic and auditable, but it still normalizes the existing pack instead of extracting from legacy/runtime sources | 🟡 Active |
| `connie-book/` can blur repo scope if left undocumented | A new in-repo planning workspace could be mistaken for part of the telco product unless kept explicitly separate | 🟡 Active |
| `connie-book/` tracker-backed flow is not yet proven repeatable | Linear-backed Symphony now reaches repo-backed workspaces and false terminal closes are auto-corrected by a repo-owned `after_run` guard, but the first clean artifact-producing `CON-6` run is still incomplete | 🟡 Active |

---

## Key Decisions Made

| Decision | Rationale | Date |
|----------|-----------|------|
| Telco is the first proof domain | One concrete target is required before generalization is meaningful | 2026-03-10 |
| The source dashboard remains the contract | The proof repo should measure against the existing dashboard, not an abstract ideal | 2026-03-10 |
| Metadata mode must be proven through the real entry point | `USE_METADATA=true streamlit run app.py` is the clearest parity check | 2026-03-10 |
| Documentation must call out proof gaps explicitly | Hidden drift or mocked verification would make future work misleading | 2026-03-10 |

---

## What Done Looks Like For This Phase

- The metadata runtime boots and validates the canonical telco pack
- Metadata mode reproduces the target shell, tabs, KPI layout, charts, and key widget surfaces
- Structural, data, and browser-level parity automation all run meaningfully
- The repo can make a narrow, defensible claim: it can reproduce the telco dashboard via metadata
- Only after that gate should broader multi-dashboard claims be considered

---

This file is the compass. If it starts claiming telco parity is proven before
the automation and browser evidence exist, it is wrong.

`connie-book/` is a parallel planning workspace. It does not change the narrow
telco proof claim or the metadata runtime scope.
