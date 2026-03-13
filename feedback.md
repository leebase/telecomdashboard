# telecom-metadata Feedback

> Review findings and follow-up items.

---

## Active Findings

1. Proof-signal cleanup is still needed.
   - The maintained metadata/data/ui suites are green, but warning noise remains.
   - `integration` markers are not yet registered in `pytest.ini`.
   - The cache layer still emits persistence warnings in some bare-script flows.

2. The parity layer is not yet trustworthy.
   - `src/ui/visual_parity.py` and `tests/visual/test_visual_parity.py` still use
     mocked screenshot behavior.
   - Passing those checks would not currently prove browser-visible parity.

3. Metadata widget coverage is incomplete.
   - The runtime handles KPI cards and charts, but required widget-slot surfaces
     still fall back to placeholders.
   - This blocks full reproduction of the target benchmark and explainer surfaces.

4. The runtime shell is still narrower than the target dashboard contract.
   - The source dashboard’s branded shell, controls, and page framing are not yet
     fully represented in metadata mode.

---

## Follow-Up Priorities

1. Fix runtime boot and validation first.
2. Replace placeholder parity code with real browser-backed checks.
3. Complete widget-slot and shell coverage for the telco proof.
4. Only then decide what abstractions are ready for non-telco use.
