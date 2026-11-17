"""Regressions for native MDI offer captions seen in WindowHub.

No GUI dependency: fake wrappers prove MDI ancestry, no arbitrary window titles.
"""
from types import SimpleNamespace

from app.agent.runtime.windowhub_mdi_native_probe import (
    _document_from_native_chain, _scoped_owner_from_native_chain, _mdi_document_classification, classify_native_candidates,
)


class Wrapper:
    def __init__(self, role, title, cls, handle, parent=None):
        self.element_info = SimpleNamespace(
            control_type=role, name=title, class_name=cls, handle=handle,
        )
        self._parent = parent

    def parent(self):
        return self._parent


def button_chain(title, host_class="MDIClient"):
    outer = Wrapper("Window", "Okna", "MainFrame", 10)
    mdi = Wrapper("Pane", "", host_class, 20, outer)
    document = Wrapper("Window", title, "AfxDocument", 30, mdi)
    toolbar = Wrapper("Pane", "", "AfxControlBar", 40, document)
    return Wrapper("Button", "Dodaj", "Button", 0, toolbar)


def test_actual_multi_number_offer_caption():
    assert _document_from_native_chain(button_chain("OFR/4488-4300 <>")) == "OFR/4488-4300 <>"


def test_previous_offer_format_remains_supported():
    assert _document_from_native_chain(button_chain("OFR/4687-")) == "OFR/4687-"


def test_zlc_never_classified_as_editable_offer():
    assert _document_from_native_chain(button_chain("ZLC/1312-")) is None


def test_matching_caption_without_mdi_structure_is_not_authorized():
    assert _document_from_native_chain(
        button_chain("OFR/4488-4300 <>", host_class="FakeContainer")
    ) is None


def test_only_one_exact_selected_caption_is_distinct():
    report = classify_native_candidates(
        selected_document="OFR/4488-4300 <>",
        candidate_ancestor_titles=(
            ("OFR/4488-4300 <>",),
            ("OFR/4488-4301 <>",),
        ),
    )
    assert report.scope_candidates == (
        "matching_mdi_ancestor", "other_mdi_ancestor",
    )
    assert report.status == "candidate_for_structural_validation"


def test_diagnostics_distinguish_active_other_order_and_unclassified():
    active = button_chain("OFR/4488-4300 <>")
    other = button_chain("OFR/4687-")
    order = button_chain("ZLC/1312-")
    unknown = button_chain("Untitled")
    for widget, expected in (
        (active, "active_offer"),
        (other, "other_offer"),
        (order, "order_read_only"),
        (unknown, "unrecognized_mdi_child"),
    ):
        assert _mdi_document_classification(widget, "OFR/4488-4300 <>") == expected


def test_no_proven_mdi_parent_stays_unclassified():
    assert _mdi_document_classification(
        button_chain("OFR/4488-4300 <>", host_class="Other"),
        "OFR/4488-4300 <>",
    ) == "no_proven_mdi_child"


def test_order_owner_is_identified_only_for_read_only_scoping():
    assert _scoped_owner_from_native_chain(
        button_chain("ZLC/1312- perfectline <>")
    ) == "ZLC/1312- perfectline <>"
    assert _scoped_owner_from_native_chain(
        button_chain("ZLC/1312-")
    ) == "ZLC/1312-"
    assert _scoped_owner_from_native_chain(
        button_chain("ZLC/1312- perfectline <>", host_class="Other")
    ) is None
    assert _document_from_native_chain(button_chain("ZLC/1312- perfectline <>")) is None


def test_unrecognized_mdi_child_has_no_scope():
    assert _scoped_owner_from_native_chain(button_chain("Unknown 123")) is None


def test_one_active_offer_with_five_orders_is_unambiguous():
    from app.agent.runtime.active_document_scope import (
        duplicate_document_action_status, unique_active_document_control,
    )
    from types import SimpleNamespace
    selected = "OFR/4488-4300 <>"
    def button(name):
        return SimpleNamespace(
            kind="button", label="Dodaj",
            metadata={"source": "windows_ui_automation", "uia_visible": True,
                      "uia_enabled": True, "document_scope": name,
                      "uia_runtime_id": name},
        )
    active = button(selected)
    orders = [button(f"ZLC/{i}-") for i in range(5)]
    tab = SimpleNamespace(
        kind="tabitem", label=selected,
        metadata={"source": "windows_ui_automation", "uia_tab_scope": "document",
                  "uia_visible": True, "uia_selected": True},
    )
    scene = SimpleNamespace(elements=(tab, active, *orders))
    status = duplicate_document_action_status(scene)
    assert status["safe_unique_active_target"] is True
    assert status["active_scope_proven"] == 1
    assert status["other_document_scope"] == 5
    assert unique_active_document_control(scene) is active


def test_unresolved_duplicate_still_blocks_add():
    from app.agent.runtime.active_document_scope import duplicate_document_action_status
    from types import SimpleNamespace
    selected = "OFR/4488-4300 <>"
    tab = SimpleNamespace(
        kind="tabitem", label=selected,
        metadata={"source": "windows_ui_automation", "uia_tab_scope": "document",
                  "uia_visible": True, "uia_selected": True},
    )
    active = SimpleNamespace(
        kind="button", label="Dodaj",
        metadata={"source": "windows_ui_automation", "uia_visible": True,
                  "uia_enabled": True, "document_scope": selected},
    )
    unknown = SimpleNamespace(
        kind="button", label="Dodaj",
        metadata={"source": "windows_ui_automation", "uia_visible": True,
                  "uia_enabled": True},
    )
    result = duplicate_document_action_status(SimpleNamespace(elements=(tab, active, unknown)))
    assert result["safe_unique_active_target"] is False
    assert result["unresolved_scope"] == 1
