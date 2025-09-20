from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from metadata_runtime.loader import MetadataLoadError, clear_cache, load_metadata


@pytest.fixture(autouse=True)
def reset_cache():
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def metadata_file(tmp_path, metadata_dict) -> Path:
    path = tmp_path / "metadata.yaml"
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata_dict, handle)
    return path


def test_load_metadata_success(metadata_file):
    first = load_metadata(metadata_file)
    second = load_metadata(metadata_file)
    assert first is second  # cache hit


def test_load_metadata_force_reload(metadata_file):
    first = load_metadata(metadata_file)
    second = load_metadata(metadata_file, force_reload=True)
    assert first is not second


def test_load_metadata_validation_error(tmp_path, metadata_dict):
    metadata_dict["kpis"][0]["metrics"][0]["data_source"] = "missing"
    path = tmp_path / "invalid.yaml"
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata_dict, handle)

    with pytest.raises(MetadataLoadError) as exc:
        load_metadata(path)

    error_payload = exc.value.errors
    assert error_payload
    assert any("missing" in json.dumps(entry) for entry in error_payload)
