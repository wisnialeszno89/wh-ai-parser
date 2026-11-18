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


def test_enrichment_diagnostic_requires_exact_selected_tab():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import diagnose_native_scope_enrichment

    scene = SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_application="Okna.exe",
                active_window_title="Okna - OFR/4680-",
            ),
            metadata={},
        ),
        elements=(),
    )
    result = diagnose_native_scope_enrichment(scene)
    assert result["status"] == "selected_tab_missing"
    assert result["native_owner_active"] == 0


def test_unknown_mdi_ancestry_explains_unrecognized_mdi_child():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import unknown_mdi_ancestry_reason

    class Node:
        def __init__(self, role, class_name, handle=0, parent=None):
            self.element_info = SimpleNamespace(
                control_type=role, class_name=class_name, handle=handle
            )
            self._parent = parent

        def parent(self):
            return self._parent

    root = Node("Window", "MainWnd", handle=100)
    mdi = Node("Pane", "MDIClient", handle=200, parent=root)
    child = Node("Window", "UnknownChild", handle=300, parent=mdi)
    target = Node("Button", "Button", parent=child)
    assert unknown_mdi_ancestry_reason(target) == "mdi_client_without_recognized_child"


def test_transient_uia_parent_wrappers_are_not_mistaken_for_cycle():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import (
        _provably_outside_mdi_client, unknown_mdi_ancestry_reason,
    )

    class Ephemeral:
        def __init__(self, depth):
            self.depth = depth
            self.element_info = SimpleNamespace(
                class_name="Toolbar", control_type="Pane", handle=0,
            )

        def parent(self):
            return Ephemeral(self.depth - 1) if self.depth else None

    # The parent() API returns brand-new wrappers. Old code kept only their
    # numeric id(), allowing CPython to recycle addresses and invent cycles.
    assert _provably_outside_mdi_client(Ephemeral(12)) is True
    assert unknown_mdi_ancestry_reason(
        Ephemeral(12)
    ) == "chain_ended_without_proven_owner"


def test_real_object_cycle_is_still_rejected():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import (
        _provably_outside_mdi_client, unknown_mdi_ancestry_reason,
    )

    class Cyclic:
        element_info = SimpleNamespace(
            class_name="Pane", control_type="Pane", handle=0,
        )

        def parent(self):
            return self

    assert _provably_outside_mdi_client(Cyclic()) is False
    assert unknown_mdi_ancestry_reason(Cyclic()) == "cyclic_parent_chain"


def test_unresolved_mdi_child_shape_is_non_authorizing_and_private():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import unresolved_mdi_child_shape

    class Node:
        def __init__(self, role, cls, handle=0, title="", parent=None):
            self.element_info = SimpleNamespace(
                control_type=role, class_name=cls, handle=handle, name=title,
            )
            self._parent = parent

        def parent(self):
            return self._parent

    root = Node("Window", "WindowRoot", 10, "Private customer")
    mdi = Node("Pane", "MDIClient", 20, parent=root)
    child = Node("Window", "AfxFrameOrView", 30, "Private customer", mdi)
    target = Node("Button", "Button", 0, "Dodaj", child)
    shape = unresolved_mdi_child_shape(target, selected="OFR/4708-")
    assert shape == {
        "kind": "mdi_immediate_child",
        "depth": 1,
        "role": "window",
        "class": "afxframeorview",
        "native_handle_present": True,
        "caption_kind": "other_or_nonstandard",
    }
    assert "Private customer" not in str(shape)
    assert "Dodaj" not in str(shape)


def test_unresolved_mdi_child_reports_nonmatching_offer_without_names():
    from types import SimpleNamespace
    from app.agent.runtime.windowhub_mdi_native_probe import unresolved_mdi_child_shape

    class Node:
        def __init__(self, role, cls, handle, title, parent=None):
            self.element_info = SimpleNamespace(
                control_type=role, class_name=cls, handle=handle, name=title,
            )
            self._parent = parent

        def parent(self):
            return self._parent

    mdi = Node("Pane", "MDIClient", 42, "")
    child = Node("Window", "MDIChild", 43, "OFR/4777-", mdi)
    button = Node("Button", "Button", 0, "Dodaj", child)
    shape = unresolved_mdi_child_shape(button, selected="OFR/4708-")
    assert shape["caption_kind"] == "offer_other"
    assert "4777" not in str(shape)
