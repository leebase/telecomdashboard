# telecom-metadata Design

## Intent

The target system is a metadata-owned dashboard runtime that can reproduce the
source telecom dashboard without relying on hand-written page code for each
subject area.

The telco dashboard is the first required proof. The runtime design should be
general enough to support later packs, but no abstraction is considered proven
until it can reproduce the telco target faithfully.

## Target Design Shape

### Metadata-Defined Shell

The runtime should be able to define, from metadata:

- sidebar controls
- theme controls
- print controls
- brand header
- global page header
- tab rail and page ordering

This is required because the source dashboard contract is not only KPI cards and
charts. Its first impression comes from the surrounding shell.

### Subject-Area Page Pattern

Most telco tabs follow one repeated pattern:

- page header row
- AI action
- time-period selector
- KPI card grid
- chart sections
- KPI detail expanders

The metadata model should express that pattern declaratively while still
allowing exceptional pages such as benchmark management.

### Widget Registry

The runtime should own a widget registry that maps metadata widget definitions
to Streamlit renderers.

Required categories for the telco proof:

- KPI cards
- line, bar, area, and distribution charts
- KPI detail expanders
- read-only tables
- editable benchmark tables
- form/editor surfaces

Using a placeholder fallback is acceptable during development, but not at the
proof gate.

### Query Compiler And Datasource Abstraction

The runtime should separate:

- metadata-defined metric intent
- SQL compilation
- datasource execution
- result transformation into widget payloads

This allows one metadata pack to drive the dashboard while execution details
remain in runtime-owned code.

### Parity Verification Strategy

Proof should be multi-layered:

1. Structural parity
   Compare tabs, labels, required controls, section counts, and widget presence.
2. Data parity
   Compare KPI values, deltas, and chart datasets between legacy and metadata paths.
3. Visual parity
   Compare browser-rendered screens against stable source-dashboard references.

All three layers are needed. A runtime that validates YAML but renders the wrong
shell, wrong values, or wrong visible layout has not reproduced the dashboard.

## Reference Target

The source visual and structural target is documented in:

- `/Users/leeharrington/projects/telecomdashboard/docs/METADATA_DRIVEN_SCREEN_SPEC.md`
- `/Users/leeharrington/projects/telecomdashboard/docs/screen-grabs/current-look/`

Those assets define what the telco proof should look like. This document defines
how `telecom-metadata` should be structured internally to achieve that outcome.
