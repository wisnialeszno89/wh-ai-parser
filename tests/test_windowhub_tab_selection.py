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



class _ElementInfo:
    def __init__(self, control_type, class_name):
        self.control_type = control_type
        self.class_name = class_name


class _Parent:
    def __init__(self, control_type, class_name):
        self.element_info = _ElementInfo(
            control_type,
            class_name,
        )


class _Tab:
    def __init__(self, parent):
        self._parent = parent

    def parent(self):
        return self._parent


def test_tab_scope_identifies_windowhub_document_tab_host():
    tab = _Tab(
        _Parent(
            "Tab",
            "Afx:TabWnd:6e0000:8:10003:10",
        )
    )

    assert (
        WindowHubUIAutomationProvider._tab_scope(tab)
        == "document"
    )


def test_tab_scope_identifies_nested_note_tab_host():
    tab = _Tab(
        _Parent(
            "Tab",
            "SysTabControl32",
        )
    )

    assert (
        WindowHubUIAutomationProvider._tab_scope(tab)
        == "nested"
    )


def test_tab_scope_does_not_classify_unknown_tab_host_as_document():
    tab = _Tab(
        _Parent(
            "Tab",
            "SomeOtherTabHost",
        )
    )

    assert (
        WindowHubUIAutomationProvider._tab_scope(tab)
        == "other"
    )
