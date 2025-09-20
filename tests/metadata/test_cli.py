from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from metadata_runtime.cli import main


@pytest.fixture
def metadata_file(tmp_path, metadata_dict) -> Path:
    path = tmp_path / "metadata.yaml"
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata_dict, handle)
    return path


def test_cli_validate_success(metadata_file, capsys):
    exit_code = main(["validate", str(metadata_file), "--quiet"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_cli_validate_failure(metadata_file, capsys, metadata_dict):
    metadata_dict["kpis"][0]["subject_area"] = "unknown"
    metadata_file.write_text(yaml.safe_dump(metadata_dict))

    exit_code = main(["validate", str(metadata_file)])
    assert exit_code == 1
    stdout, stderr = capsys.readouterr()
    assert "Metadata validation failed" in stderr


def test_cli_validate_json_output(metadata_file, capsys, metadata_dict):
    metadata_dict["kpis"][0]["metrics"][0]["data_source"] = "missing"
    metadata_file.write_text(yaml.safe_dump(metadata_dict))

    exit_code = main(["validate", str(metadata_file), "--json"])
    assert exit_code == 1
    stdout, stderr = capsys.readouterr()
    error_payload = json.loads(stderr)
    assert isinstance(error_payload, list)
