from __future__ import annotations

import pytest

from metadata_runtime.models import MetadataConfig


def test_metadata_config_valid(metadata_dict):
    config = MetadataConfig.parse_obj(metadata_dict)
    assert config.pack_id == "test_pack"
    assert config.subject_areas[0].id == "network"
    assert config.kpis[0].id == "kpi_network_availability"


def test_metadata_config_subject_area_collision(metadata_dict):
    metadata_dict["subject_areas"].append(metadata_dict["subject_areas"][0])

    with pytest.raises(ValueError) as exc:
        MetadataConfig.parse_obj(metadata_dict)

    assert "Subject area IDs must be unique" in str(exc.value)


def test_metadata_config_invalid_filter_binding(metadata_dict):
    metadata_dict["filters"]["global"][0]["bindings"] = {"start_param": "start"}

    with pytest.raises(ValueError) as exc:
        MetadataConfig.parse_obj(metadata_dict)

    assert "Date range filters require start/end bindings" in str(exc.value)
