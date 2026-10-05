from __future__ import annotations

from dataclasses import dataclass

from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)


@dataclass
class FakeInterfaceSelectionItem:
    CurrentIsSelected: bool


@dataclass
class FakeElement:
    iface_selection_item: object | None = None

    def get_properties(self):
        return {}


def test_selection_state_reads_selection_item_pattern():
    element = FakeElement(
        iface_selection_item=FakeInterfaceSelectionItem(
            CurrentIsSelected=True
        )
    )

    assert (
        WindowHubUIAutomationProvider._selection_state(element)
        is True
    )


def test_selection_state_returns_false_for_unselected_tab():
    element = FakeElement(
        iface_selection_item=FakeInterfaceSelectionItem(
            CurrentIsSelected=False
        )
    )

    assert (
        WindowHubUIAutomationProvider._selection_state(element)
        is False
    )


def test_selection_state_returns_none_when_not_exposed():
    element = FakeElement()

    assert (
        WindowHubUIAutomationProvider._selection_state(element)
        is None
    )
