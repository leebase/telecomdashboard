# telecom-metadata Project Description

`telecom-metadata` is a proof repo for rebuilding a concrete telecom KPI
dashboard from metadata instead of bespoke page code.

This repository is not yet a clean, fully general metadata platform. It still
contains the inherited dashboard runtime in `app.py`, and the metadata runtime
is layered into that codebase through a feature flag and a metadata-only app
path. The telco dashboard is the first proof domain, not just an example.

What already exists:

- metadata models, loader, CLI, dialect support, query compiler, datasource
  abstraction, provider, layout engine, and widget registry
- a canonical telco metadata pack in `metadata/dashboard_telco.yaml`
- metadata-focused tests for schema, queries, views, provider behavior, and UI plumbing

What is not yet proven:

- clean metadata boot in the pinned environment
- full shell and widget parity with the source dashboard
- trustworthy structural, data, and visual verification strong enough to claim success

The purpose of this repo is to close that gap. If telco parity becomes
defensible here, the runtime can then be generalized deliberately rather than
assumed to be general-purpose.
