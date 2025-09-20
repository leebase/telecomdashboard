# Contributing – Metadata Runtime

## Workflow
1. Branch from `main` with descriptive name (`feature/metadata-widgets`).
2. Update or add metadata packs under `metadata/` and supporting docs.
3. Run validation + tests before pushing:
   ```bash
   python -m metadata_cli validate metadata/dashboard_telco.yaml
   pytest tests/metadata -v
   pytest tests/ui/test_layout_engine.py -v
   pytest tests/visual/test_visual_parity.py -m visual
   ```
4. Submit PR with checklist (see below). Use draft mode until visual parity passes.

## Coding Standards
- Python: Black + isort (`make lint`), 4-space indent, type hints required in new modules.
- YAML: 2-space indent, double quotes only when interpolation or commas required.
- SQL templates: Prefer uppercase keywords, lowercase columns, Jinja macros for filters.
- Tests: Use pytest markers (`metadata`, `integration`, `visual`). Provide fixtures under `tests/fixtures/`.

## Metadata Guidelines
- Every KPI must define owner, description, thresholds (where meaningful), cache TTL, and explicit dataset references.
- Use comments sparingly for assumptions; replace with real values once data is confirmed.
- Keep packs under 500 lines by extracting shared structures (macros, auxiliary metrics).
- Update `docs/CONFIGURE.md` when introducing new metadata features or CLI commands.

## PR Checklist
- [ ] Metadata validated (`metadata_cli validate`).
- [ ] All tests passing (`pytest`).
- [ ] Visual snapshots updated or reviewed.
- [ ] Documentation updated (schema/config/runbook as needed).
- [ ] Feature flag impact described (does it require toggle?).
- [ ] Rollback plan noted in PR body.

## Review Expectations
- At least one reviewer from Data Engineering and one from UI Systems.
- Review focus: schema compatibility, security (SQL injection, access control), UX parity, regression risk.
- Use comment tags (`[blocking]`, `[nit]`, `[suggestion]`) to classify feedback.

## Release Notes
- Update `CHANGELOG.md` under “Unreleased” with bullet describing metadata change.
- Tag pack with `metadata/<pack_id>@vX.Y.Z` git tag after merge.

## Open Items
- Document Storybook-style component tests once layout interpreter lands.
- Automate PR template updates for metadata-specific checklist.
