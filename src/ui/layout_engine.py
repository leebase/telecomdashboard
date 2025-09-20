"""Render metadata-driven layouts using Streamlit components."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Dict, Tuple

import streamlit as st

from metadata_runtime.models import LayoutSection, SubjectAreaConfig
from ui.metadata_widgets import render_widget

SlotResolver = Callable[[str, str], Tuple[str, Dict]]


@contextmanager
def _no_op_context():  # pragma: no cover - fallback for testing
    yield


def render_subject_area(area: SubjectAreaConfig, resolve_slot: SlotResolver) -> None:
    """Render a subject area using metadata layout definitions."""
    layout = area.layout

    for section in layout.sections:
        if section.title:
            st.subheader(section.title)

        for row in section.rows:
            columns = st.columns(len(row)) if row else []
            if not columns:
                continue

            for column, slot in zip(columns, row):
                slot_dict = {k: v for k, v in slot.dict().items() if v}
                if not slot_dict:
                    continue
                slot_type, slot_value = next(iter(slot_dict.items()))
                if not slot_value:
                    continue
                widget_type, payload = resolve_slot(slot_type, slot_value)
                context_manager = column if hasattr(column, "__enter__") else _no_op_context()
                with context_manager:
                    render_widget(widget_type, payload)
