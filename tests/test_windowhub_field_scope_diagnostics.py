from types import SimpleNamespace

from tools.diagnose_windowhub_field_scope import _field_diagnostic


def make_field(*, value, metadata, label="Szerokość", scope=None, status="unknown"):
    element = SimpleNamespace(metadata=metadata)
    return SimpleNamespace(
        label=label,
        control_type="edit",
        document_scope=scope,
        scope_status=status,
        value=value,
        element=element,
    )


def test_field_scope_diagnostic_never_includes_observed_field_value():
    field = make_field(
        value="CUSTOMER-SECRET-1234",
        metadata={
            "uia_window_handle": 123,
            "uia_ancestor_context": (
                ("Pane", "Afx:Pane", "CUSTOMER-SECRET-ANCESTOR"),
            ),
            "document_scope": None,
            "uia_tab_scope": None,
        },
    )

    result = _field_diagnostic(field, root_handle=123)
    rendered = repr(result)

    assert result["label"] == "Szerokość"
    assert result["scope_status"] == "unknown"
    assert result["current_value_present"] is True
    # The wrapper used for enumeration is not proof of the control's native
    # HWND ancestry. With no native HWND, root membership must stay unknown.
    assert result["enumerated_by_observed_window"] is True
    assert result["uia_native_handle_present"] is False
    assert result["native_window_relation_available"] is False
    assert result["in_observed_root_window"] is None
    assert result["ancestor_structure"] == ["Pane<Afx:Pane>"]
    assert "CUSTOMER-SECRET-1234" not in rendered
    assert "CUSTOMER-SECRET-ANCESTOR" not in rendered


def test_field_scope_diagnostic_distinguishes_unobserved_value_and_other_window():
    field = make_field(
        value=None,
        metadata={
            "uia_window_handle": 456,
            "uia_owned_modal": True,
            "uia_ancestor_context": (),
        },
    )

    result = _field_diagnostic(field, root_handle=123)

    assert result["current_value_present"] is False
    assert result["enumerated_by_observed_window"] is False
    assert result["in_observed_root_window"] is None
    assert result["owned_modal"] is True
    assert result["ancestor_structure"] == []


def test_native_relationships_are_reported_separately_from_enumeration():
    field = make_field(
        value="1200",
        metadata={
            "uia_window_handle": 123,
            "uia_native_handle": 901,
            "document_scope": None,
        },
    )
    native_relationships = {
        "uia_native_handle_present": True,
        "native_window_relation_available": True,
        "native_root_matches_observed_window": False,
        "native_root_owner_matches_observed_window": True,
        "native_parent_matches_observed_window": False,
        "native_owner_matches_observed_window": False,
        "in_observed_root_window": False,
        "native_owned_by_observed_window": True,
        "belongs_to_observed_window_or_owned_popup": True,
    }

    result = _field_diagnostic(
        field,
        root_handle=123,
        native_relationships=native_relationships,
    )

    assert result["enumerated_by_observed_window"] is True
    assert result["uia_native_handle_present"] is True
    assert result["native_window_relation_available"] is True
    assert result["native_root_matches_observed_window"] is False
    assert result["native_root_owner_matches_observed_window"] is True
    assert result["in_observed_root_window"] is False
    assert result["native_owned_by_observed_window"] is True
    assert result["belongs_to_observed_window_or_owned_popup"] is True
    # Window ownership alone is not enough to claim a document-tab scope.
    assert result["document_scope"] is None
    assert result["scope_status"] == "unknown"


def test_active_document_ancestor_match_is_reported_without_emitting_ancestor_name():
    secret_name = "OFR/4304-4103"
    field = make_field(
        value="SENSITIVE-CURRENT-VALUE",
        metadata={
            "uia_ancestor_context": (
                ("Window", "Afx:TabChild", secret_name),
                ("Pane", "Afx:Pane", "Private customer context"),
            ),
            "uia_native_handle": 701,
            "uia_window_handle": 123,
        },
    )

    result = _field_diagnostic(
        field,
        root_handle=123,
        active_document=secret_name,
        native_relationships={
            "uia_native_handle_present": True,
            "native_window_relation_available": True,
            "native_root_matches_observed_window": True,
            "native_root_owner_matches_observed_window": True,
            "native_parent_matches_observed_window": False,
            "native_owner_matches_observed_window": False,
            "in_observed_root_window": True,
            "native_owned_by_observed_window": True,
            "belongs_to_observed_window_or_owned_popup": True,
        },
    )

    rendered = repr(result)
    assert result["active_document_ancestor_name_exact_match"] is True
    assert result["active_document_window_ancestor_name_exact_match"] is True
    assert result["named_window_ancestor_count"] == 1
    assert secret_name not in rendered
    assert "Private customer context" not in rendered
    assert "SENSITIVE-CURRENT-VALUE" not in rendered


def test_document_ancestor_match_requires_exact_name_and_reports_unmatched():
    field = make_field(
        value="SENSITIVE-CURRENT-VALUE",
        metadata={
            "uia_ancestor_context": (
                ("Window", "Afx:TabChild", "OFR/4304-4103 other"),
                ("Pane", "Afx:Pane", "OFR/4304-4103"),
            ),
        },
    )

    result = _field_diagnostic(
        field,
        root_handle=123,
        active_document="OFR/4304-4103",
        native_relationships={
            "uia_native_handle_present": False,
            "native_window_relation_available": False,
            "native_root_matches_observed_window": None,
            "native_root_owner_matches_observed_window": None,
            "native_parent_matches_observed_window": None,
            "native_owner_matches_observed_window": None,
            "in_observed_root_window": None,
            "native_owned_by_observed_window": None,
            "belongs_to_observed_window_or_owned_popup": None,
        },
    )

    assert result["active_document_ancestor_name_exact_match"] is True
    assert result["active_document_window_ancestor_name_exact_match"] is False
    assert result["named_window_ancestor_count"] == 1


def test_selected_tab_native_handle_correlation_is_boolean_only():
    field = make_field(
        value="DO-NOT-PRINT-THIS",
        metadata={
            "uia_native_handle": 701,
            "uia_window_handle": 123,
            "uia_ancestor_context": (
                ("Pane", "Afx:Pane", "Parent", 501),
                ("Window", "Afx:TabChild", "Child", 123),
            ),
        },
    )

    result = _field_diagnostic(
        field,
        root_handle=123,
        selected_document_tab_native_handle=501,
    )

    rendered = repr(result)
    assert result["selected_document_tab_native_handle_present"] is True
    assert result["field_native_handle_present"] is True
    assert result["field_native_handle_matches_selected_document_tab"] is False
    assert result["ancestor_native_handle_available_count"] == 2
    assert result["ancestor_native_handle_matches_selected_document_tab"] is True
    assert "DO-NOT-PRINT-THIS" not in rendered
    for raw_handle in ("701", "501", "123"):
        assert raw_handle not in rendered
    # Native-handle equality is just a diagnostic clue; scope remains unknown.
    assert result["scope_status"] == "unknown"
    assert result["document_scope"] is None


def test_tab_native_handle_correlation_stays_unknown_when_tab_handle_missing():
    field = make_field(
        value="DO-NOT-PRINT-THIS",
        metadata={
            "uia_native_handle": 701,
            "uia_ancestor_context": (
                ("Window", "Afx:TabChild", "Child", 123),
            ),
        },
    )

    result = _field_diagnostic(field, selected_document_tab_native_handle=None)

    assert result["selected_document_tab_native_handle_present"] is False
    assert result["field_native_handle_matches_selected_document_tab"] is None
    assert result["ancestor_native_handle_matches_selected_document_tab"] is None
    assert result["scope_status"] == "unknown"
    assert result["document_scope"] is None


def test_field_scope_diagnostic_preserves_explicit_document_scope():
    field = make_field(
        value="1200",
        scope="OFR/4297",
        status="active_document",
        metadata={
            "document_scope": "OFR/4297",
            "uia_tab_scope": None,
            "uia_document_tab_selected": None,
        },
    )

    result = _field_diagnostic(field, root_handle=123)

    assert result["document_scope"] == "OFR/4297"
    assert result["scope_status"] == "active_document"
