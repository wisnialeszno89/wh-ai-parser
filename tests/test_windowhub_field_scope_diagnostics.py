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
    assert result["in_observed_root_window"] is True
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
    assert result["in_observed_root_window"] is False
    assert result["owned_modal"] is True
    assert result["ancestor_structure"] == []


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
