"""Regressions for native MDI offer captions seen in WindowHub.

No GUI dependency: fake wrappers prove MDI ancestry, no arbitrary window titles.
"""
from types import SimpleNamespace

from app.agent.runtime.windowhub_mdi_native_probe import (
    _document_from_native_chain, classify_native_candidates,
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
