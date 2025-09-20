from __future__ import annotations

from typing import Dict, Tuple

import pytest

from metadata_runtime.models import LayoutConfig, LayoutSection, LayoutSlot, SubjectAreaConfig
from ui import layout_engine


class DummyColumn:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture(autouse=True)
def patch_streamlit(monkeypatch):
    monkeypatch.setattr(layout_engine.st, "subheader", lambda *args, **kwargs: None)
    monkeypatch.setattr(layout_engine.st, "columns", lambda n: [DummyColumn() for _ in range(n)])


def test_render_subject_area_invokes_resolver(monkeypatch):
    calls: list[Tuple[str, Dict]] = []

    def fake_render(widget_type, payload):
        calls.append((widget_type, payload))

    monkeypatch.setattr(layout_engine, "render_widget", fake_render)

    area = SubjectAreaConfig(
        id="network",
        title="Network",
        layout=LayoutConfig(
            sections=[
                LayoutSection(
                    id="cards",
                    rows=[
                        [LayoutSlot(kpi_card="kpi_network_availability")],
                        [LayoutSlot(chart="chart_latency_trend")],
                    ],
                )
            ]
        ),
    )

    def resolver(slot_type: str, slot_value: str):
        return slot_type, {"id": slot_value}

    layout_engine.render_subject_area(area, resolver)

    assert calls == [
        ("kpi_card", {"id": "kpi_network_availability"}),
        ("chart", {"id": "chart_latency_trend"}),
    ]
