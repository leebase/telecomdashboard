# telecomdashboard Project Definition

> Compatibility alias for projects that expect `project-definition.md`.
>
> For this repo, this file mirrors the product scope captured in
> `product-definition.md`. Keep the two files aligned.

---

## Project Summary

`telecomdashboard` is a telecom KPI dashboard for reviewing operational
performance across network, customer, revenue, usage, and operations domains,
with optional AI-generated insights and benchmark context.

---

## Primary Users

- Internal telecom operators or consulting teams reviewing KPI performance
- Stakeholders who need a polished dashboard for demos, diagnostics, or executive discussion
- Developers maintaining the data, UI, and AI-assisted analysis workflows

---

## Core User Jobs

- Inspect KPI performance by business pillar
- Compare recent trends and regional variation
- Generate narrative insights and recommended actions from current KPI data
- Present findings with theme-aware, client-ready visuals

---

## Current Project Scope

### In Scope

- Streamlit dashboard in `app.py`
- Local SQLite and CSV-backed telecom data model
- Theme switching and print/export-friendly presentation
- AI insights workflow using configured LLM access
- Benchmark, health, config, logging, and security support modules

### Not Yet Confirmed As Core Product

- The separate multi-agent playbook prioritization prototype in `runAgentsApp.py`
- Packaging the dashboard as a polished installable CLI or library

---

## Revival Success Criteria

- A new contributor can set up and run the main dashboard from the repo docs
- The dashboard works without needing to reverse-engineer legacy files
- AI-dependent features fail gracefully when secrets or providers are unavailable
- The repo clearly distinguishes active product surfaces from experiments

---

## Non-Goals For The Revival Phase

- Reinventing the product from scratch
- Adding major new features before the current system is verified
- Treating every historical prototype as equally important

---

Use this document to keep scope anchored on the main dashboard until the human says otherwise.
