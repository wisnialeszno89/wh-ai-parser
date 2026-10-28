from types import SimpleNamespace

import pytest

from app.runtime.execution.vision.bridges.execution_safety_gate import (
    ExecutionSafetyGate,
)


def _gate(
    metadata,
    *,
    capability="selectable",
    confidence=0.9,
    source="windowhub_ui_automation",
):
    values = {
        "source": source,
        "uia_enabled": True,
        "uia_visible": True,
        "uia_control_type": "tabitem",
        "uia_tab_scope": "document",
        "uia_document_tab_selected": False,
    }
    values.update(metadata)
    return ExecutionSafetyGate().can_execute_uia_element(
        metadata=values,
        interaction_capability=SimpleNamespace(value=capability),
        interaction_capability_confidence=confidence,
        window_handle=123,
        require_foreground=False,
    )


@pytest.mark.parametrize("selected", [True, False])
def test_safety_gate_allows_selectable_verified_windowhub_document_tab(selected):
    assert _gate({"uia_document_tab_selected": selected}) is True


def test_safety_gate_keeps_clickable_button_support():
    assert _gate(
        {
            "uia_control_type": "button",
            "uia_tab_scope": None,
            "uia_document_tab_selected": None,
        },
        capability="clickable",
    ) is True


@pytest.mark.parametrize(
    "metadata",
    [
        {"uia_tab_scope": None},
        {"uia_document_tab_selected": None},
        {"uia_control_type": "button"},
        {"source": "windows_ui_automation"},
    ],
)
def test_safety_gate_rejects_selectable_controls_outside_windowhub_document_tabs(metadata):
    assert _gate(metadata) is False


@pytest.mark.parametrize(
    "metadata",
    [
        {"uia_enabled": False},
        {"uia_visible": False},
    ],
)
def test_safety_gate_still_requires_visible_and_enabled_tab(metadata):
    assert _gate(metadata) is False


def test_safety_gate_still_requires_positive_capability_confidence():
    assert _gate({}, confidence=0.0) is False
