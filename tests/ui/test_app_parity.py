from __future__ import annotations

import os

from streamlit.testing.v1 import AppTest


def _run_app(use_metadata: bool) -> AppTest:
    os.environ["USE_METADATA"] = "true" if use_metadata else "false"
    at = AppTest.from_file("app.py")
    at.run(timeout=20)
    return at


def _run_metadata_only_app() -> AppTest:
    at = AppTest.from_file("apps/meta/app.py")
    at.run(timeout=20)
    return at


def test_legacy_and_metadata_shell_match():
    legacy = _run_app(use_metadata=False)
    metadata = _run_app(use_metadata=True)

    assert len(legacy.exception) == 0
    assert len(metadata.exception) == 0
    assert [tab.label for tab in legacy.tabs] == [tab.label for tab in metadata.tabs]
    assert [box.label for box in legacy.sidebar.selectbox] == [box.label for box in metadata.sidebar.selectbox]
    assert [button.label for button in legacy.sidebar.button] == [button.label for button in metadata.sidebar.button]
    assert [header.value for header in legacy.header] == [header.value for header in metadata.header]


def test_metadata_time_period_controls_cover_standard_tabs():
    legacy = _run_app(use_metadata=False)
    metadata = _run_app(use_metadata=True)

    legacy_selector_keys = sorted(
        selectbox.key
        for selectbox in legacy.selectbox
        if selectbox.key and selectbox.key.startswith("time_period_selector_")
    )
    metadata_selector_keys = sorted(
        selectbox.key
        for selectbox in metadata.selectbox
        if selectbox.key and selectbox.key.startswith("time_period_selector_")
    )

    assert metadata_selector_keys == legacy_selector_keys


def test_metadata_benchmark_tab_renders_metadata_owned_widgets():
    metadata = _run_metadata_only_app()

    assert len(metadata.exception) == 0
    assert any(header.value == "🎯 Benchmark Management" for header in metadata.header)
    assert any(subheader.value == "Benchmarks" for subheader in metadata.subheader)
    assert any(subheader.value == "✏️ Edit Individual KPI" for subheader in metadata.subheader)
    assert any(selectbox.key == "metadata_benchmark_kpi" for selectbox in metadata.selectbox)
    assert any(selectbox.key == "metadata_benchmark_direction" for selectbox in metadata.selectbox)
