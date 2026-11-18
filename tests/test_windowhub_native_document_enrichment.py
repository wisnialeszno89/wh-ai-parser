"""Native MDI ownership enrichment is fail-closed and independent of button order."""
from types import SimpleNamespace as NS
from unittest.mock import patch

import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.windowhub_mdi_native_probe import (
    enrich_native_mdi_document_scope, _document_from_native_chain,
)
from app.agent.runtime.active_document_scope import unique_active_document_control


def wrap(name="", role="pane", cls="", handle=1, parent=None, rid=None):
    obj = NS(element_info=NS(
        name=name, control_type=role, class_name=cls, handle=handle,
    ), rid=rid)
    obj.parent = lambda: parent
    return obj


def tree(owner, *, rid="A", mdi_host=True, host_handle=44, child_handle=45):
    host = wrap("MDI Client", cls="MDIClient" if mdi_host else "Unrelated", handle=host_handle)
    doc = wrap(owner, role="window", cls="Afx:MDIChild", handle=child_handle, parent=host)
    bar = wrap("Toolbar", cls="Afx:ControlBar", handle=46, parent=doc)
    return wrap("Dodaj", role="button", cls="Button", handle=47, parent=bar, rid=rid)


def scene(*buttons, active="OFR/4678-", title="Okna - OFR/4678-"):
    tab = ScreenElement(
        kind="tabitem", label=active, x=1, y=1, width=20, height=15,
        metadata={
            "source": "windows_ui_automation", "uia_visible": True,
            "uia_selected": True, "uia_tab_scope": "document",
        },
    )
    elements = (tab,) + tuple(
        ScreenElement(
            kind="button", label="Dodaj", x=i*30, y=20, width=20, height=20,
            metadata={
                "source": "windows_ui_automation", "uia_visible": True,
                "uia_enabled": True, "uia_runtime_id": rid,
                "document_scope": None,
            },
        ) for i, rid in enumerate(buttons)
    )
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe", active_window_title=title
            ),
            metadata={"window_handle": 123},
        ),
        elements=elements,
    )


class FakeDesktop:
    def __init__(self, descendants):
        self.descendants_value = descendants

    def window(self, *, handle):
        assert handle == 123
        return NS(wrapper_object=lambda: NS(
            descendants=lambda: self.descendants_value
        ))


def scope(original, wrappers, *, win32=None):
    with patch(
        "app.agent.perception.windowhub_ui_automation_provider.WindowHubUIAutomationProvider._runtime_id",
        side_effect=lambda obj: obj.rid,
    ):
        return enrich_native_mdi_document_scope(
            original, desktop=FakeDesktop(wrappers), win32=win32
        )


def test_realistic_mdi_client_structure_is_recognized():
    assert _document_from_native_chain(tree("OFR/4678-")) == "OFR/4678-"
    assert _document_from_native_chain(tree("OFR/4678-", mdi_host=False)) is None


def test_two_documents_scoped_and_only_current_dodaj_is_targetable():
    before = scene("A", "B")
    after = scope(before, [tree("OFR/4678-", rid="A"), tree("OFR/4670-", rid="B")])
    assert after is not before
    assert [e.metadata.get("document_scope") for e in after.elements[1:]] == [
        "OFR/4678-", "OFR/4670-"
    ]
    assert unique_active_document_control(after) is after.elements[1]


def test_missing_native_ancestor_refuses_all_scopes():
    before = scene("A", "B")
    after = scope(before, [tree("OFR/4678-", rid="A"), tree("Bad Screen", rid="B")])
    assert after is before
    assert unique_active_document_control(after) is None


def test_duplicate_matching_active_owners_refused():
    before = scene("A", "B")
    after = scope(before, [tree("OFR/4678-", rid="A"), tree("OFR/4678-", rid="B")])
    assert after is before


def test_wrong_active_title_refuses_native_owner():
    before = scene("A", active="OFR/4678-", title="Okna - OFR/4670-")
    assert scope(before, [tree("OFR/4678-", rid="A")]) is before


def test_duplicate_uia_runtime_identity_refused():
    before = scene("A")
    assert scope(before, [tree("OFR/4678-", rid="A"), tree("OFR/4678-", rid="A")]) is before


def test_existing_contradictory_scope_refused():
    from dataclasses import replace
    before = scene("A")
    elements = list(before.elements)
    elements[1] = replace(elements[1], metadata={
        **elements[1].metadata, "document_scope": "OFR/4670-"
    })
    before = replace(before, elements=tuple(elements))
    assert scope(before, [tree("OFR/4678-", rid="A")]) is before


class FakeWin32:
    def __init__(self):
        self.parents = {44: 123, 45: 44, 52: 44, 47: 45, 54: 52}
        self.active_handles = iter((45, 45))
        self.captions = {45: "OFR/4678-", 123: "Okna - OFR/4678-"}

    def parent(self, hwnd, relationship):
        if relationship == 2:
            return self.parents.get(self.parents.get(hwnd), self.parents.get(hwnd))
        assert relationship == 1
        return self.parents.get(hwnd)

    def foreground(self):
        return 123

    def active_child(self, host):
        assert host == 44
        return next(self.active_handles)

    def class_name(self, hwnd):
        return "MDIClient" if hwnd == 44 else "Other"

    def title(self, hwnd):
        return self.captions.get(hwnd, "")


def sibling_buttons():
    active = tree("OFR/4678-", rid="A")
    untitled = tree("", rid="B", child_handle=52)
    untitled.element_info.handle = 54
    return active, untitled


def test_untitled_sibling_of_the_win32_active_offer_can_be_excluded():
    active, untitled = sibling_buttons()
    others = [tree(f"OFR/{index}-", rid=str(index)) for index in range(1, 6)]
    after = scope(scene("B", "1", "A", "2", "3", "4", "5"),
                  [*others, active, untitled], win32=FakeWin32())
    assert unique_active_document_control(after).metadata["uia_runtime_id"] == "A"
    assert after.elements[1].metadata["document_scope_source"] == "verified_inactive_mdi_sibling"


@pytest.mark.parametrize("disagreement", [
    "wrong_child", "no_active_child", "active_switch", "native_title",
    "native_parent", "wrong_host", "foreground", "same_active_child",
])
def test_untitled_control_blocks_if_the_win32_proof_does_not_agree(disagreement):
    active, untitled = sibling_buttons()
    api = FakeWin32()
    if disagreement == "wrong_child":
        api.active_handles = iter((52, 52))
    elif disagreement == "no_active_child":
        api.active_handles = iter((0, 0))
    elif disagreement == "active_switch":
        api.active_handles = iter((45, 52))
    elif disagreement == "native_title":
        api.captions[45] = "OFR/9999-"
    elif disagreement == "native_parent":
        api.parents[54] = 45
    elif disagreement == "wrong_host":
        untitled.parent().parent().parent().element_info.handle = 500
    elif disagreement == "foreground":
        api.foreground = lambda: 111
    elif disagreement == "same_active_child":
        untitled.parent().parent().element_info.handle = 45
        api.parents[54] = 45
    before = scene("A", "B")
    assert scope(before, [untitled, active], win32=api) is before
    assert unique_active_document_control(before) is None


@pytest.mark.parametrize("hit_case, allowed", [
    ("exact", True), ("different_runtime", False),
    ("different_document", False), ("inactive_document", False),
])
def test_hit_requires_the_same_runtime_and_current_mdi_child(hit_case, allowed):
    from app.agent.runtime.windowhub_mdi_native_probe import verify_mdi_add_hit

    hit, _ = sibling_buttons()
    api = FakeWin32()
    hit.element_info.runtime_id = (1, 2)
    hit.element_info.automation_id = "button-id"
    hit.element_info.visible = hit.element_info.enabled = True
    if hit_case == "different_runtime":
        hit.element_info.runtime_id = (1, 3)
    elif hit_case == "different_document":
        api.captions[123] = "Okna - OFR/200-"
    elif hit_case == "inactive_document":
        api.active_handles = iter((52,))
    assert verify_mdi_add_hit(
        (300, 400), root=123, expected_offer="OFR/4678-",
        metadata={"automation_id": "button-id", "uia_runtime_id": "1-2"},
        desktop=NS(from_point=lambda x, y: hit), win32=api,
    ) is allowed
