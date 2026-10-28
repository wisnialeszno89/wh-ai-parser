from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.windowhub_mdi_tab_activator import (
    WM_MDIACTIVATE,
    WM_MDIGETACTIVE,
    activate_windowhub_mdi_document_tab,
)


@dataclass
class FakeElementInfo:
    name: str
    control_type: str
    class_name: str = ""
    handle: int = 0
    visible: bool = True
    enabled: bool = True


class FakeSelectionItem:
    def __init__(self, item):
        self.item = item

    @property
    def CurrentIsSelected(self):
        override = self.item.state.get("selection_override", {}).get(
            self.item.element_info.name
        )
        if isinstance(override, bool):
            return override
        return (
            self.item.state["active"]
            == self.item.document_child_handle
        )


class FakeUIAElement:
    def __init__(
        self,
        state,
        name,
        control_type,
        *,
        class_name="",
        handle=0,
        document_child_handle=0,
    ):
        self.state = state
        self.element_info = FakeElementInfo(
            name=name,
            control_type=control_type,
            class_name=class_name,
            handle=handle,
        )
        self._parent = None
        self._children = []
        self.document_child_handle = document_child_handle

    def add(self, child):
        child._parent = self
        self._children.append(child)
        return child

    def parent(self):
        return self._parent

    def children(self):
        return tuple(self._children)

    def descendants(self):
        result = []
        for child in self._children:
            result.append(child)
            result.extend(child.descendants())
        return tuple(result)

    def window_text(self):
        return self.element_info.name

    @property
    def iface_selection_item(self):
        if self.element_info.control_type.casefold() != "tabitem":
            raise AttributeError("SelectionItemPattern unavailable")
        if self.state.get("selection_unavailable"):
            raise AttributeError("SelectionItemPattern unavailable")
        return FakeSelectionItem(self)


class FakeWindowSpec:
    def __init__(self, element):
        self.element = element

    def wrapper_object(self):
        return self.element


class FakeDesktop:
    def __init__(self, root):
        self.root = root

    def window(self, *, handle):
        assert handle == self.root.element_info.handle
        return FakeWindowSpec(self.root)


@dataclass
class Fixture:
    desktop: FakeDesktop
    state: dict
    calls: list[tuple[int, int, int, int]]
    root_handle: int = 100
    mdi_handle: int = 200
    start1_handle: int = 300
    offer_handle: int = 301


def build_fixture(
    *,
    active=301,
    selection_override=None,
    duplicate_start1=False,
    selection_unavailable=False,
):
    state = {
        "active": active,
        "selection_override": dict(selection_override or {}),
        "selection_unavailable": selection_unavailable,
    }
    root = FakeUIAElement(
        state, "Okna - Test", "Window", class_name="WindowHubMain", handle=100
    )
    mdi = root.add(
        FakeUIAElement(state, "", "Pane", class_name="MDIClient", handle=200)
    )
    host = mdi.add(
        FakeUIAElement(
            state, "", "Tab", class_name="Afx:TabWnd:6e0000:8:10003:10", handle=201
        )
    )
    host.add(
        FakeUIAElement(
            state, "Start1", "TabItem", document_child_handle=300
        )
    )
    if duplicate_start1:
        host.add(
            FakeUIAElement(
                state, "Start1", "TabItem", document_child_handle=300
            )
        )
    host.add(
        FakeUIAElement(
            state,
            "OFR/4005--3937-3707N <>",
            "TabItem",
            document_child_handle=301,
        )
    )
    mdi.add(
        FakeUIAElement(
            state, "Start1", "Window", class_name="MDIChild", handle=300
        )
    )
    mdi.add(
        FakeUIAElement(
            state,
            "OFR/4005--3937-3707N <>",
            "Window",
            class_name="MDIChild",
            handle=301,
        )
    )

    calls = []

    def send_message(hwnd, message, wparam, lparam):
        calls.append((hwnd, message, wparam, lparam))
        if message == WM_MDIGETACTIVE:
            return state["active"]
        if message == WM_MDIACTIVATE:
            assert lparam == 0
            state["active"] = wparam
            return 0
        raise AssertionError(f"Unexpected message: {message}")

    return Fixture(
        desktop=FakeDesktop(root),
        state=state,
        calls=calls,
    ), send_message


def activate(fixture, send_message, *, live, foreground=True):
    return activate_windowhub_mdi_document_tab(
        target_label="Start1",
        window_handle=fixture.root_handle,
        live=live,
        desktop_factory=lambda: fixture.desktop,
        message_sender=send_message,
        foreground_checker=lambda _root: foreground,
        timeout_seconds=0.2,
    )


def test_dry_run_validates_native_mdi_target_without_activating_it():
    fixture, send_message = build_fixture()

    result = activate(fixture, send_message, live=False)

    assert result.success is True
    assert result.executed is False
    assert result.active_before_target is False
    assert result.active_after_target is False
    assert fixture.state["active"] == fixture.offer_handle
    assert not any(call[1] == WM_MDIACTIVATE for call in fixture.calls)


def test_live_activation_sends_one_mdi_message_and_verifies_both_states():
    fixture, send_message = build_fixture()

    result = activate(fixture, send_message, live=True)

    assert result.success is True
    assert result.executed is True
    assert result.before_selected is False
    assert result.after_selected is True
    assert result.active_before_target is False
    assert result.active_after_target is True
    assert fixture.state["active"] == fixture.start1_handle
    activation_calls = [call for call in fixture.calls if call[1] == WM_MDIACTIVATE]
    assert len(activation_calls) == 1
    assert activation_calls[0] == (
        fixture.mdi_handle,
        WM_MDIACTIVATE,
        fixture.start1_handle,
        0,
    )


def test_activation_fails_closed_when_document_tab_is_ambiguous():
    fixture, send_message = build_fixture(duplicate_start1=True)

    result = activate(fixture, send_message, live=True)

    assert result.success is False
    assert result.executed is False
    assert "exactly one" in result.reason
    assert fixture.state["active"] == fixture.offer_handle
    assert not any(call[1] == WM_MDIACTIVATE for call in fixture.calls)


def test_activation_fails_closed_when_uia_and_mdi_states_conflict():
    fixture, send_message = build_fixture(
        active=300,
        selection_override={"Start1": False},
    )

    result = activate(fixture, send_message, live=True)

    assert result.success is False
    assert result.executed is False
    assert "conflicts" in result.reason
    assert fixture.state["active"] == 300
    assert not any(call[1] == WM_MDIACTIVATE for call in fixture.calls)


def test_activation_fails_closed_if_windowhub_is_not_foreground():
    fixture, send_message = build_fixture()

    result = activate(fixture, send_message, live=True, foreground=False)

    assert result.success is False
    assert result.executed is False
    assert "not the foreground" in result.reason
    assert fixture.state["active"] == fixture.offer_handle
    assert not any(call[1] == WM_MDIACTIVATE for call in fixture.calls)

def test_live_activation_uses_native_mdi_state_when_uia_selection_is_unavailable():
    fixture, send_message = build_fixture(selection_unavailable=True)

    result = activate(fixture, send_message, live=True)

    assert result.success is True
    assert result.executed is True
    assert result.before_selected is None
    assert result.after_selected is None
    assert result.active_before_target is False
    assert result.active_after_target is True
    assert "selection state is unavailable" in result.reason
    assert fixture.state["active"] == fixture.start1_handle
    assert sum(call[1] == WM_MDIACTIVATE for call in fixture.calls) == 1


def test_already_active_native_target_succeeds_without_uia_selection_pattern():
    fixture, send_message = build_fixture(
        active=300,
        selection_unavailable=True,
    )

    result = activate(fixture, send_message, live=True)

    assert result.success is True
    assert result.executed is False
    assert result.before_selected is None
    assert result.active_before_target is True
    assert result.active_after_target is True
    assert not any(call[1] == WM_MDIACTIVATE for call in fixture.calls)
