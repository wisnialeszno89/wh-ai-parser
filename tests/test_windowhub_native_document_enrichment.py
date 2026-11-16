"""Native MDI ownership enrichment is fail-closed and independent of button order."""
from types import SimpleNamespace as NS
from unittest.mock import patch

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


def tree(owner, *, rid="A", mdi_host=True):
    host = wrap("MDI Client", cls="MDIClient" if mdi_host else "Unrelated", handle=44)
    doc = wrap(owner, role="window", cls="Afx:MDIChild", handle=45, parent=host)
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


def scope(original, wrappers):
    with patch(
        "app.agent.perception.windowhub_ui_automation_provider.WindowHubUIAutomationProvider._runtime_id",
        side_effect=lambda obj: obj.rid,
    ):
        return enrich_native_mdi_document_scope(
            original, desktop=FakeDesktop(wrappers)
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
