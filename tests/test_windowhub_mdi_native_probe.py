"""No action is permitted by native ancestry diagnostics alone."""
from app.agent.runtime.windowhub_mdi_native_probe import (
    classify_native_candidates,
    native_title_matches,
)


def test_exact_native_mdi_caption_matching():
    assert native_title_matches("OFR/4680-", " OFR/4680- ")
    assert not native_title_matches("OFR/4680-", "OFR/4678-")
    assert not native_title_matches("OFR/4680-", "Document OFR/4680-")
    assert not native_title_matches("", "OFR/4680-")


def test_no_title_only_evidence_does_not_promote_action():
    result = classify_native_candidates(
        selected_document="OFR/4680-",
        candidate_ancestor_titles=(
            ("", "Main Window"),
            ("", "Main Window"),
            ("", "Main Window"),
        ),
    )
    assert result.status == "native_mdi_scope_unresolved"
    assert result.unknown_buttons == 3


def test_multiple_matching_ancestors_are_ambiguous():
    result = classify_native_candidates(
        selected_document="OFR/4680-",
        candidate_ancestor_titles=(
            ("OFR/4680-", "OFR/4680-"),
            ("OFR/4670-",),
        ),
    )
    assert result.status == "native_mdi_scope_unresolved"


def test_single_candidate_still_requires_structural_validation():
    result = classify_native_candidates(
        selected_document="OFR/4680-",
        candidate_ancestor_titles=(
            ("OFR/4670-",),
            ("OFR/4680-",),
            ("OFR/4678-",),
        ),
    )
    assert result.status == "candidate_for_structural_validation"
    assert result.scope_candidates == (
        "other_mdi_ancestor", "matching_mdi_ancestor", "other_mdi_ancestor"
    )
    # Not equivalent to verified UIA-document scope or permission to click.


def test_proven_global_toolbar_is_outside_mdi():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import _provably_outside_mdi_client

    class Node:
        def __init__(self, class_name, parent=None):
            self.element_info = SimpleNamespace(class_name=class_name)
            self._parent = parent

        def parent(self):
            return self._parent

    root = Node("Window")
    toolbar = Node("Toolbar", root)
    global_button = Node("Button", toolbar)
    assert _provably_outside_mdi_client(global_button) is True
    mdi = Node("MDIClient", root)
    document = Node("Window", mdi)
    offer_button = Node("Button", document)
    assert _provably_outside_mdi_client(offer_button) is False


def test_unfinished_or_broken_ancestry_is_not_proof():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import _provably_outside_mdi_client

    class Broken:
        element_info = SimpleNamespace(class_name="Button")

        def parent(self):
            raise ValueError("provider failed")

    assert _provably_outside_mdi_client(Broken()) is False
