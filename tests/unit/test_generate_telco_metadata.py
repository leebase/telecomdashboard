from pathlib import Path

import yaml

from tools.generate_telco_metadata import (
    GENERATOR_VERSION,
    build_generator_inventory,
    extract_section_contracts,
    extract_tab_labels,
    file_sha256,
    generate_pack_from_legacy,
    write_generator_inventory,
)


def test_generate_pack_from_legacy_is_deterministic(tmp_path):
    input_path = tmp_path / "dashboard_telco.yaml"
    output_a = tmp_path / "generated_a.yaml"
    output_b = tmp_path / "generated_b.yaml"
    app_path = tmp_path / "app.py"

    input_path.write_text(
        """
schema_version: "1.0"
pack_id: telecom_default
label: Telecom KPI Dashboard
metadata_sources:
  changelog: docs/CHANGELOG.md
  generated_on: "2025-08-10"
  generated_by: tooling/autogen
  source_version: Sprint 4
subject_areas: []
""".lstrip(),
        encoding="utf-8",
    )
    app_path.write_text(
        """
import streamlit as st

tab1 = st.tabs([
    "📡 Network Performance",
])
""".lstrip(),
        encoding="utf-8",
    )

    generate_pack_from_legacy(input_path, output_a, app_path=app_path)
    generate_pack_from_legacy(input_path, output_b, app_path=app_path)

    assert output_a.read_text(encoding="utf-8") == output_b.read_text(encoding="utf-8")

    generated = yaml.safe_load(output_a.read_text(encoding="utf-8"))

    assert generated["metadata_sources"] == {
        "changelog": "docs/CHANGELOG.md",
        "generated_by": "tools/generate_telco_metadata.py",
        "generator_version": GENERATOR_VERSION,
        "generator_mode": "normalize_existing_pack_with_legacy_tab_contract",
        "legacy_tab_contract_sha256": file_sha256(app_path),
        "source_pack_sha256": file_sha256(input_path),
    }


def test_generate_pack_preserves_existing_pack_content(tmp_path):
    input_path = tmp_path / "dashboard_telco.yaml"
    output_path = tmp_path / "generated.yaml"

    input_path.write_text(
        """
schema_version: "1.0"
pack_id: telecom_default
label: Telecom KPI Dashboard
filters:
  global:
    - id: date_range
      type: date_range
metadata_sources:
  generated_on: "2025-08-10"
subject_areas:
  - id: network_performance
    title: Network Performance
""".lstrip(),
        encoding="utf-8",
    )

    generate_pack_from_legacy(input_path, output_path)
    generated = yaml.safe_load(output_path.read_text(encoding="utf-8"))

    assert generated["pack_id"] == "telecom_default"
    assert generated["filters"]["global"][0]["id"] == "date_range"
    assert generated["subject_areas"][0]["id"] == "network_performance"
    assert "generated_on" not in generated["metadata_sources"]


def test_generate_pack_applies_legacy_tab_titles_and_order(tmp_path):
    input_path = tmp_path / "dashboard_telco.yaml"
    output_path = tmp_path / "generated.yaml"
    app_path = tmp_path / "app.py"

    input_path.write_text(
        """
schema_version: "1.0"
pack_id: telecom_default
label: Telecom KPI Dashboard
subject_areas:
  - id: benchmark_management
    title: Benchmarks
    order: 99
  - id: network_performance
    title: Network
    order: 42
    layout:
      sections:
        - id: np_cards
          title: Key KPIs
        - id: np_trends
          title: Trends
        - id: np_details
          title: Detail
  - id: customer_experience
    title: CX
    order: 12
    layout:
      sections:
        - id: cx_cards
          title: Key KPIs
        - id: cx_trends
          title: Trends
  - id: custom_subject_area
    title: Custom
""".lstrip(),
        encoding="utf-8",
    )
    app_path.write_text(
        """
import streamlit as st

tab1, tab2, tab3 = st.tabs([
    "📡 Network Performance",
    "😊 Customer Experience",
    "🎯 Benchmark Management",
])


def render_network_performance(data):
    st.header("📡 Network Performance & Reliability")
    st.subheader("📈 Network Performance Trends")
    st.subheader("📘 Detailed KPI Information")


def render_customer_experience(data, db):
    st.header("😊 Customer Experience & Retention")
    st.subheader("📈 Customer Experience Trends")
""".lstrip(),
        encoding="utf-8",
    )

    generate_pack_from_legacy(input_path, output_path, app_path=app_path)
    generated = yaml.safe_load(output_path.read_text(encoding="utf-8"))

    assert [subject_area["id"] for subject_area in generated["subject_areas"]] == [
        "network_performance",
        "customer_experience",
        "benchmark_management",
        "custom_subject_area",
    ]
    assert [subject_area["title"] for subject_area in generated["subject_areas"]] == [
        "📡 Network Performance",
        "😊 Customer Experience",
        "🎯 Benchmark Management",
        "Custom",
    ]
    assert [subject_area["order"] for subject_area in generated["subject_areas"]] == [1, 2, 3, 4]
    assert generated["subject_areas"][0]["layout"]["sections"][1]["title"] == "📈 Network Performance Trends"
    assert generated["subject_areas"][0]["layout"]["sections"][2]["title"] == "📘 Detailed KPI Information"
    assert generated["subject_areas"][1]["layout"]["sections"][1]["title"] == "📈 Customer Experience Trends"


def test_extract_tab_labels_from_legacy_app(tmp_path):
    app_path = tmp_path / "app.py"
    app_path.write_text(
        """
import streamlit as st

tab1, tab2 = st.tabs([
    "📡 Network Performance",
    "🎯 Benchmark Management",
])
""".lstrip(),
        encoding="utf-8",
    )

    assert extract_tab_labels(app_path) == [
        "📡 Network Performance",
        "🎯 Benchmark Management",
    ]


def test_extract_section_contracts_from_legacy_app(tmp_path):
    app_path = tmp_path / "app.py"
    app_path.write_text(
        """
import streamlit as st


def render_network_performance(data):
    st.header("📡 Network Performance & Reliability")
    st.subheader("📈 Network Performance Trends")
    st.subheader("📘 Detailed KPI Information")


def render_operational_efficiency(data, db):
    st.header("🛠️ Operational Efficiency")
    st.subheader("📈 Operational Trends")
""".lstrip(),
        encoding="utf-8",
    )

    assert extract_section_contracts(app_path) == {
        "network_performance": {
            "function": "render_network_performance",
            "header": "📡 Network Performance & Reliability",
            "sections": [
                "📈 Network Performance Trends",
                "📘 Detailed KPI Information",
            ],
        },
        "operational_efficiency": {
            "function": "render_operational_efficiency",
            "header": "🛠️ Operational Efficiency",
            "sections": ["📈 Operational Trends"],
        },
    }


def test_write_generator_inventory_includes_expected_sources(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "app.py").write_text(
        """
import streamlit as st

tab1, tab2, tab3 = st.tabs([
    "📡 Network Performance",
    "😊 Customer Experience",
    "🎯 Benchmark Management",
])


def render_network_performance(data):
    st.header("📡 Network Performance & Reliability")
    st.subheader("📈 Network Performance Trends")


def render_customer_experience(data, db):
    st.header("😊 Customer Experience & Retention")
    st.subheader("📈 Customer Experience Trends")
""".lstrip(),
        encoding="utf-8",
    )

    inventory_path = tmp_path / "inventory.yaml"
    write_generator_inventory(inventory_path, repo_root)

    inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))

    assert inventory == {
        "generator_inputs": {
            "legacy_tabs": [
                "📡 Network Performance",
                "😊 Customer Experience",
                "🎯 Benchmark Management",
            ],
            "legacy_section_contracts": {
                "network_performance": {
                    "function": "render_network_performance",
                    "header": "📡 Network Performance & Reliability",
                    "sections": ["📈 Network Performance Trends"],
                },
                "customer_experience": {
                    "function": "render_customer_experience",
                    "header": "😊 Customer Experience & Retention",
                    "sections": ["📈 Customer Experience Trends"],
                },
            },
            "source_files": [
                {
                    "path": "app.py",
                    "role": "Legacy Streamlit tab contract and section headings",
                },
                {
                    "path": "benchmark_manager.py",
                    "role": "Benchmark management tab structure and export/import affordances",
                },
                {
                    "path": "database_connection.py",
                    "role": "Legacy KPI/query patterns that still inform proof-pack semantics",
                },
                {
                    "path": "scripts/create_views.py",
                    "role": "SQLite view surface used by the maintained metadata proof path",
                },
            ],
        }
    }

    assert build_generator_inventory(repo_root) == inventory
