from pathlib import Path

import yaml

from tools.generate_telco_metadata import (
    GENERATOR_VERSION,
    file_sha256,
    generate_pack_from_legacy,
)


def test_generate_pack_from_legacy_is_deterministic(tmp_path):
    input_path = tmp_path / "dashboard_telco.yaml"
    output_a = tmp_path / "generated_a.yaml"
    output_b = tmp_path / "generated_b.yaml"

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

    generate_pack_from_legacy(input_path, output_a)
    generate_pack_from_legacy(input_path, output_b)

    assert output_a.read_text(encoding="utf-8") == output_b.read_text(encoding="utf-8")

    generated = yaml.safe_load(output_a.read_text(encoding="utf-8"))

    assert generated["metadata_sources"] == {
        "changelog": "docs/CHANGELOG.md",
        "generated_by": "tools/generate_telco_metadata.py",
        "generator_version": GENERATOR_VERSION,
        "generator_mode": "normalize_existing_pack",
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
