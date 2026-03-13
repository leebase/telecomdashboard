# telecom-metadata Project Definition

> Compatibility alias for projects that expect `project-definition.md`.
>
> For this repo, this file mirrors the product scope captured in
> `product-definition.md`. Keep the two files aligned.

---

## Project Summary

`telecom-metadata` is a metadata-driven dashboard runtime intended to recreate
the existing telecom KPI dashboard first, then generalize only after parity is
verified.

---

## Primary Users

- Developers building and validating the metadata runtime
- Teams proving dashboard reproduction from metadata
- Stakeholders deciding whether the runtime is credible enough to generalize

---

## Core User Jobs

- Express dashboard structure and data binding in metadata
- Render a concrete dashboard experience from a metadata pack
- Verify parity between the source dashboard and the metadata-driven output
- Decide when the runtime is strong enough to support broader reuse

---

## Current Project Scope

### In Scope

- Metadata runtime modules and metadata-mode app paths
- Canonical telco proof pack
- Structural, data, and visual verification for telco parity
- Legacy dashboard path only as the comparison target

### Explicit First Proof Domain

- The telco KPI dashboard carried into this repo from the source project

### Not Yet Confirmed As Core Product

- Broad cross-domain dashboard support
- Verified general-purpose metadata generation from arbitrary apps
- A complete parity claim for the current runtime

---

## Success Criteria For This Phase

- Metadata validation and runtime boot work in the supported local environment
- Telco metadata pack renders the intended shell and content surface
- Parity can be demonstrated through meaningful automation and browser checks
- Claims about the repo match the actual proof evidence

---

## Non-Goals For This Phase

- Overstating cross-industry capability
- Treating partial metadata rendering as final proof
- Removing the legacy comparison surface before proof is complete

---

Use this document to keep scope anchored on telco parity proof.
