from types import SimpleNamespace

from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)

from tools.diagnose_windowhub_field_scope import (
    _field_diagnostic,
    _field_document_window_geometry,
    _field_coordinate_origin_probe,
    _native_child_window_control_census,
    _native_control_document_context_census,
    _native_field_hwnd_geometry_census,
    _native_document_window_geometry_summary,
    _native_window_title_matches,
    _uia_native_document_control_correlation_census,
)


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


def test_native_document_child_window_title_probe_returns_only_sanitized_counts():
    document_label = "OFR/4306-4235 <>"
    windows = (
        {
            "handle": 501,
            "title": document_label,
            "class_name": "Afx:MDIChild",
            "visible": True,
        },
        {
            "handle": 502,
            "title": "Podgląd wydruku <OFR/4306-4235 <>",
            "class_name": "WindowsForms10.Window",
            "visible": True,
        },
        {
            "handle": 503,
            "title": "Inna oferta",
            "class_name": "Afx:MDIChild",
            "visible": False,
        },
    )

    exact, summary = _native_window_title_matches(document_label, windows)

    assert tuple(item["handle"] for item in exact) == (501,)
    assert summary == {
        "available": True,
        "descendant_native_window_count": 3,
        "active_document_exact_title_match_count": 1,
        "active_document_substring_title_match_count": 2,
    }
    rendered = repr(summary)
    assert document_label not in rendered
    assert "Podgląd wydruku" not in rendered
    assert "501" not in rendered


def test_native_document_child_window_probe_stays_unknown_when_snapshot_unavailable():
    exact, summary = _native_window_title_matches(
        "OFR/4306-4235",
        None,
    )

    assert exact == ()
    assert summary == {
        "available": False,
        "descendant_native_window_count": None,
        "active_document_exact_title_match_count": None,
        "active_document_substring_title_match_count": None,
    }


def test_native_child_window_matches_are_boolean_only_and_do_not_assign_scope(monkeypatch):
    # Keep this unit test independent from unrelated HWNDs on the runner.
    monkeypatch.setattr(
        "tools.diagnose_windowhub_field_scope._native_parent_chain",
        lambda _handle: None,
    )
    active_document = "OFR/4306-4235"
    field = make_field(
        value="DO-NOT-PRINT-THIS",
        metadata={
            "uia_native_handle": 701,
            "uia_ancestor_context": (
                ("Window", "Afx:MDIChild", active_document, 501),
            ),
        },
    )

    result = _field_diagnostic(
        field,
        active_document=active_document,
        exact_active_document_window_handles=(501,),
        native_child_window_probe_available=True,
    )

    rendered = repr(result)
    assert result["field_or_ancestor_handle_matches_active_document_title_window"] is True
    assert result["native_parent_chain_matches_active_document_title_window"] is None
    assert result["scope_status"] == "unknown"
    assert result["document_scope"] is None
    assert "DO-NOT-PRINT-THIS" not in rendered
    assert active_document not in rendered
    assert "501" not in rendered
    assert "701" not in rendered


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


def _geometry_test_field(bounds):
    if bounds is None:
        x = y = width = height = None
    else:
        x, y, width, height = bounds
    return SimpleNamespace(
        label="PRIVATE_FIELD_LABEL",
        value="PRIVATE_FIELD_VALUE",
        element=SimpleNamespace(x=x, y=y, width=width, height=height),
    )


def _geometry_test_document_window(
    *, visible=True, client_bounds_screen=(120, 180, 420, 480)
):
    return {
        "handle": 987654,
        "title": "PRIVATE_ACTIVE_DOCUMENT",
        "class_name": "Afx:MDIChild",
        "visible": visible,
        "client_bounds_screen": client_bounds_screen,
    }


_GEOMETRY_TEST_ROOT_RECT = SimpleNamespace(left=100, top=100)


def test_document_geometry_reports_containment_without_exposing_identity_or_bounds():
    result = _field_document_window_geometry(
        _geometry_test_field((40, 100, 100, 30)),
        exact_active_document_windows=(_geometry_test_document_window(),),
        root_window_rect=_GEOMETRY_TEST_ROOT_RECT,
    )

    assert result == {
        "active_document_client_geometry_available": True,
        "field_bounds_fully_within_active_document_client_area": True,
        "field_bounds_intersect_active_document_client_area": True,
    }
    rendered = repr(result)
    for private_value in (
        "PRIVATE_FIELD_LABEL",
        "PRIVATE_FIELD_VALUE",
        "PRIVATE_ACTIVE_DOCUMENT",
        "987654",
        "120",
        "180",
        "420",
        "480",
    ):
        assert private_value not in rendered


def test_document_geometry_distinguishes_partial_overlap_from_full_containment():
    result = _field_document_window_geometry(
        _geometry_test_field((280, 110, 60, 30)),
        exact_active_document_windows=(_geometry_test_document_window(),),
        root_window_rect=_GEOMETRY_TEST_ROOT_RECT,
    )

    assert result["active_document_client_geometry_available"] is True
    assert result["field_bounds_fully_within_active_document_client_area"] is False
    assert result["field_bounds_intersect_active_document_client_area"] is True


def test_document_geometry_marks_nonoverlapping_field_outside_client_area():
    result = _field_document_window_geometry(
        _geometry_test_field((400, 120, 40, 20)),
        exact_active_document_windows=(_geometry_test_document_window(),),
        root_window_rect=_GEOMETRY_TEST_ROOT_RECT,
    )

    assert result["active_document_client_geometry_available"] is True
    assert result["field_bounds_fully_within_active_document_client_area"] is False
    assert result["field_bounds_intersect_active_document_client_area"] is False


def test_document_geometry_stays_unknown_without_unique_visible_window_and_bounds():
    cases = (
        (
            _geometry_test_field((40, 100, 100, 30)),
            (_geometry_test_document_window(), _geometry_test_document_window()),
            _GEOMETRY_TEST_ROOT_RECT,
        ),
        (
            _geometry_test_field((40, 100, 100, 30)),
            (_geometry_test_document_window(visible=False),),
            _GEOMETRY_TEST_ROOT_RECT,
        ),
        (
            _geometry_test_field((40, 100, 100, 30)),
            (_geometry_test_document_window(client_bounds_screen=None),),
            _GEOMETRY_TEST_ROOT_RECT,
        ),
        (
            _geometry_test_field(None),
            (_geometry_test_document_window(),),
            _GEOMETRY_TEST_ROOT_RECT,
        ),
    )
    expected = {
        "active_document_client_geometry_available": False,
        "field_bounds_fully_within_active_document_client_area": None,
        "field_bounds_intersect_active_document_client_area": None,
    }
    for field, windows, root_rect in cases:
        assert _field_document_window_geometry(
            field,
            exact_active_document_windows=windows,
            root_window_rect=root_rect,
        ) == expected


def test_document_geometry_summary_emits_counts_only():
    result = _native_document_window_geometry_summary((
        _geometry_test_document_window(),
        _geometry_test_document_window(
            visible=False,
            client_bounds_screen=None,
        ),
    ))

    assert result == {
        "exact_title_match_count": 2,
        "visible_exact_title_match_count": 1,
        "client_bounds_available_exact_title_match_count": 1,
    }
    rendered = repr(result)
    assert "PRIVATE_ACTIVE_DOCUMENT" not in rendered
    assert "987654" not in rendered



def test_coordinate_origin_probe_uses_windowrect_dimensions_and_distinguishes_origins():
    field = SimpleNamespace(
        label="PRIVATE_FIELD",
        value="PRIVATE_VALUE",
        element=SimpleNamespace(x=15, y=60, width=20, height=20),
        document_scope=None,
        scope_status="unknown",
    )
    window = {
        "handle": 456789,
        "title": "PRIVATE_DOCUMENT",
        "visible": True,
        "client_bounds_screen": (120, 180, 420, 480),
    }
    # Match the real WindowRect shape: left/top/width/height, without
    # right/bottom properties.
    root = SimpleNamespace(left=100, top=100, width=800, height=600)

    result = _field_coordinate_origin_probe(
        field,
        exact_active_document_windows=(window,),
        root_window_rect=root,
        root_client_bounds_screen=(110, 130, 890, 690),
    )

    assert result == {
        "available": True,
        "root_relative_intersects": False,
        "screen_relative_intersects": False,
        "root_client_relative_intersects": True,
    }
    assert "PRIVATE_FIELD" not in repr(result)
    assert "PRIVATE_VALUE" not in repr(result)
    assert "PRIVATE_DOCUMENT" not in repr(result)
    assert "456789" not in repr(result)
    assert "15" not in repr(result)
    assert field.document_scope is None
    assert field.scope_status == "unknown"


def test_coordinate_origin_probe_stays_unknown_without_unique_visible_client():
    field = SimpleNamespace(
        value="PRIVATE_VALUE",
        element=SimpleNamespace(x=1, y=1, width=20, height=20),
    )
    root = SimpleNamespace(left=0, top=0, right=100, bottom=100)
    base_window = {
        "visible": True,
        "client_bounds_screen": (0, 0, 50, 50),
    }

    assert _field_coordinate_origin_probe(
        field,
        exact_active_document_windows=(base_window, base_window),
        root_window_rect=root,
        root_client_bounds_screen=(0, 0, 100, 100),
    ) == {
        "available": False,
        "root_relative_intersects": None,
        "screen_relative_intersects": None,
        "root_client_relative_intersects": None,
    }
    assert _field_coordinate_origin_probe(
        field,
        exact_active_document_windows=({
            "visible": False,
            "client_bounds_screen": (0, 0, 50, 50),
        },),
        root_window_rect=root,
        root_client_bounds_screen=(0, 0, 100, 100),
    )["available"] is False


def test_native_child_window_control_census_reports_class_counts_only():
    windows = (
        {
            "handle": 101,
            "title": "PRIVATE WINDOW TEXT",
            "class_name": "Edit",
            "visible": True,
            "client_bounds_screen": (10, 10, 120, 35),
        },
        {
            "handle": 102,
            "title": "",
            "class_name": "ComboBox",
            "visible": True,
            "client_bounds_screen": (10, 40, 120, 70),
        },
        {
            "handle": 103,
            "title": "PRIVATE MFC WINDOW",
            "class_name": "Afx:MDIChild",
            "visible": False,
            "client_bounds_screen": None,
        },
        {
            "handle": 104,
            "title": "",
            "class_name": "WindowsForms10.EDIT.app.0",
            "visible": True,
            "client_bounds_screen": (20, 80, 130, 105),
        },
        {
            "handle": 105,
            "title": "",
            "class_name": None,
            "visible": False,
            "client_bounds_screen": None,
        },
    )

    result = _native_child_window_control_census(windows)

    assert result["available"] is True
    assert result["descendant_count"] == 5
    assert result["field_like_native_control_count"] == 3
    assert result["by_class"]["win32_edit"] == {
        "count": 1,
        "visible_count": 1,
        "positive_bounds_count": 1,
        "native_text_present_count": 1,
    }
    assert result["by_class"]["win32_combobox"] == {
        "count": 1,
        "visible_count": 1,
        "positive_bounds_count": 1,
        "native_text_present_count": 0,
    }
    assert result["by_class"]["afx_mfc"]["count"] == 1
    assert result["by_class"]["windows_forms_edit"]["count"] == 1
    assert result["by_class"]["class_unavailable"]["count"] == 1

    rendered = repr(result)
    for private_value in (
        "PRIVATE WINDOW TEXT",
        "PRIVATE MFC WINDOW",
        "101",
        "102",
        "103",
        "104",
        "105",
        "10",
        "120",
        "Afx:MDIChild",
    ):
        assert private_value not in rendered


def test_native_child_window_control_census_fails_closed_without_snapshot():
    assert _native_child_window_control_census(None) == {
        "available": False,
        "descendant_count": None,
        "field_like_native_control_count": None,
        "by_class": {},
    }

def test_native_field_hwnd_geometry_census_correlates_handles_and_sanitizes_output():
    field = SimpleNamespace(
        label="PRIVATE_FIELD_LABEL",
        value="PRIVATE_FIELD_VALUE",
        element=SimpleNamespace(
            x=40, y=80, width=100, height=30,
            metadata={"uia_native_handle": 501},
        ),
    )
    native_windows = (
        {
            "handle": 501,
            "title": "PRIVATE_WINDOW_TITLE",
            "class_name": "Edit",
            "visible": True,
            "client_bounds_screen": (145, 190, 250, 225),
        },
        {
            "handle": 502,
            "title": "PRIVATE_OTHER",
            "class_name": "ComboBox",
            "visible": True,
            "client_bounds_screen": (500, 500, 600, 540),
        },
    )
    root = SimpleNamespace(left=100, top=100, width=800, height=600)

    result = _native_field_hwnd_geometry_census(
        (field,),
        native_windows,
        root_window_rect=root,
        root_client_bounds_screen=(110, 130, 890, 690),
    )

    assert result["available"] is True
    assert result["fields_considered"] == 1
    assert result["fields_with_native_handle_count"] == 1
    assert result["field_handle_matches_native_descendant_count"] == 1
    assert result["matched_native_visible_count"] == 1
    assert result["matched_native_bounds_available_count"] == 1
    assert result["paired_geometry_available_count"] == 1
    assert result["root_relative_intersects_count"] == 1
    assert result["screen_relative_intersects_count"] == 0
    assert result["root_client_relative_intersects_count"] == 1
    assert result["edge_alignment_tolerance_px"] == (2, 4, 8, 16, 32)
    assert result["root_relative_edges_within_tolerance_counts"] == {
        "2": 0, "4": 0, "8": 0, "16": 1, "32": 1,
    }
    assert result["screen_relative_edges_within_tolerance_counts"] == {
        "2": 0, "4": 0, "8": 0, "16": 0, "32": 0,
    }
    assert result["root_client_relative_edges_within_tolerance_counts"] == {
        "2": 0, "4": 0, "8": 0, "16": 0, "32": 1,
    }
    assert result["matched_native_class_buckets"]["win32_edit"] == 1
    rendered = repr(result)
    for private_value in (
        "PRIVATE_FIELD_LABEL",
        "PRIVATE_FIELD_VALUE",
        "PRIVATE_WINDOW_TITLE",
        "PRIVATE_OTHER",
        "501",
        "502",
        "145",
        "190",
    ):
        assert private_value not in rendered
    assert field.element.metadata["uia_native_handle"] == 501


def test_native_field_hwnd_geometry_census_fails_closed_without_snapshot():
    field = SimpleNamespace(
        label="PRIVATE",
        value="PRIVATE",
        element=SimpleNamespace(
            x=1, y=2, width=10, height=10,
            metadata={"uia_native_handle": 501},
        ),
    )

    result = _native_field_hwnd_geometry_census(
        (field,),
        None,
        root_window_rect=SimpleNamespace(left=0, top=0),
    )
    assert result["available"] is False
    assert result["fields_considered"] == 1
    assert result["field_handle_matches_native_descendant_count"] is None
    assert "PRIVATE" not in repr(result)
    assert "501" not in repr(result)

def test_native_field_hwnd_geometry_edge_alignment_distinguishes_origins():
    field = SimpleNamespace(
        label="PRIVATE_FIELD",
        value="PRIVATE_VALUE",
        element=SimpleNamespace(
            x=40, y=80, width=100, height=30,
            metadata={"uia_native_handle": 501},
        ),
    )
    windows = ({
        "handle": 501,
        "title": "PRIVATE_TITLE",
        "class_name": "Edit",
        "visible": True,
        # Root screen origin is (100, 100). Translating the native bounds
        # by that origin makes all four edges match the UIA field exactly.
        "client_bounds_screen": (140, 180, 240, 210),
    },)
    root = SimpleNamespace(left=100, top=100, width=800, height=600)

    result = _native_field_hwnd_geometry_census(
        (field,),
        windows,
        root_window_rect=root,
        root_client_bounds_screen=(110, 130, 890, 690),
    )

    assert result["root_relative_edges_within_tolerance_counts"] == {
        "2": 1, "4": 1, "8": 1, "16": 1, "32": 1,
    }
    assert result["screen_relative_edges_within_tolerance_counts"] == {
        "2": 0, "4": 0, "8": 0, "16": 0, "32": 0,
    }
    assert result["root_client_relative_edges_within_tolerance_counts"] == {
        "2": 0, "4": 0, "8": 0, "16": 0, "32": 1,
    }
    rendered = repr(result)
    for private_value in (
        "PRIVATE_FIELD",
        "PRIVATE_VALUE",
        "PRIVATE_TITLE",
        "501",
        "140",
        "180",
    ):
        assert private_value not in rendered

def test_native_control_document_context_census_reports_relationship_counts_only(monkeypatch):
    parent_chains = {
        11: (11, 50, 100),
        12: (12, 100),
    }
    monkeypatch.setattr(
        "tools.diagnose_windowhub_field_scope._native_parent_chain",
        lambda handle: parent_chains.get(handle),
    )
    document = {
        "handle": 50,
        "title": "PRIVATE_ACTIVE_DOCUMENT_TITLE",
        "class_name": "Afx:MDIChild",
        "visible": True,
        "client_bounds_screen": (100, 180, 400, 400),
    }
    windows = (
        {
            "handle": 11,
            "title": "PRIVATE_EDIT_TITLE",
            "class_name": "Edit",
            "visible": True,
            "client_bounds_screen": (120, 200, 200, 230),
        },
        {
            "handle": 12,
            "title": "PRIVATE_COMBO_TITLE",
            "class_name": "ComboBox",
            "visible": True,
            "client_bounds_screen": (500, 500, 600, 550),
        },
        {
            "handle": 13,
            "title": "PRIVATE_HIDDEN_EDIT",
            "class_name": "Edit",
            "visible": False,
            "client_bounds_screen": (130, 240, 220, 270),
        },
        document,
    )

    result = _native_control_document_context_census(
        windows,
        (document,),
        observed_root_handle=100,
    )

    assert result["available"] is True
    assert result["native_descendant_count"] == 4
    assert result["field_like_native_control_count"] == 3
    assert result["visible_field_like_native_control_count"] == 2
    assert result["visible_field_like_with_bounds_count"] == 2
    assert result["document_window_identity_available"] is True
    assert result["document_client_bounds_available"] is True
    assert result["visible_field_like_parent_chain_checked_count"] == 2
    assert result["visible_field_like_parent_chain_contains_document_count"] == 1
    assert result["visible_field_like_parent_chain_excludes_document_count"] == 1
    assert result["visible_field_like_parent_chain_contains_root_count"] == 2
    assert result["visible_field_like_bounds_intersect_document_client_count"] == 1
    assert result["visible_field_like_bounds_fully_within_document_client_count"] == 1
    assert result["visible_field_like_parent_and_bounds_match_count"] == 1
    assert result["by_class"]["win32_edit"] == {
        "count": 2,
        "visible_count": 1,
        "positive_bounds_count": 2,
        "visible_parent_chain_checked_count": 1,
        "visible_parent_chain_contains_document_count": 1,
        "visible_parent_chain_excludes_document_count": 0,
        "visible_parent_chain_contains_root_count": 1,
        "visible_bounds_intersect_document_client_count": 1,
        "visible_bounds_fully_within_document_client_count": 1,
    }
    assert result["by_class"]["win32_combobox"]["count"] == 1
    assert result["by_class"]["win32_combobox"]["visible_parent_chain_excludes_document_count"] == 1

    rendered = repr(result)
    for private_value in (
        "PRIVATE_ACTIVE_DOCUMENT_TITLE",
        "PRIVATE_EDIT_TITLE",
        "PRIVATE_COMBO_TITLE",
        "PRIVATE_HIDDEN_EDIT",
        "100",
        "120",
        "180",
        "200",
        "230",
        "400",
        "500",
        "600",
        "(120, 200",
    ):
        assert private_value not in rendered
    assert "handle" not in rendered.casefold()


def test_native_control_document_context_census_fails_closed_without_unique_visible_document(monkeypatch):
    monkeypatch.setattr(
        "tools.diagnose_windowhub_field_scope._native_parent_chain",
        lambda _handle: None,
    )
    edit = {
        "handle": 11,
        "title": "PRIVATE_EDIT",
        "class_name": "Edit",
        "visible": True,
        "client_bounds_screen": (10, 20, 100, 40),
    }
    hidden_document = {
        "handle": 50,
        "title": "PRIVATE_DOCUMENT",
        "class_name": "Afx:MDIChild",
        "visible": False,
        "client_bounds_screen": (0, 0, 200, 200),
    }

    result = _native_control_document_context_census(
        (edit, hidden_document),
        (hidden_document,),
        observed_root_handle=100,
    )

    assert result["available"] is True
    assert result["document_window_identity_available"] is False
    assert result["document_client_bounds_available"] is False
    assert result["visible_field_like_parent_chain_checked_count"] == 0
    assert result["visible_field_like_parent_chain_contains_document_count"] == 0
    assert result["visible_field_like_bounds_intersect_document_client_count"] == 0
    assert result["visible_field_like_parent_and_bounds_match_count"] == 0
    rendered = repr(result)
    assert "PRIVATE_EDIT" not in rendered
    assert "PRIVATE_DOCUMENT" not in rendered
    assert "11" not in rendered
    assert "50" not in rendered

def test_uia_native_field_geometry_correlation_matches_bounds_without_handles(monkeypatch):
    from tools.diagnose_windowhub_field_scope import (
        _uia_native_field_geometry_correlation_census,
    )

    monkeypatch.setattr(
        "tools.diagnose_windowhub_field_scope._native_parent_chain",
        lambda handle: {
            11: (11, 50, 100),
            12: (12, 100),
        }.get(handle),
    )
    document = {
        "handle": 50,
        "title": "PRIVATE_DOCUMENT",
        "class_name": "Afx:MDIChild",
        "visible": True,
        "client_bounds_screen": (100, 100, 500, 500),
    }
    native_windows = (
        {
            "handle": 11,
            "title": "PRIVATE_EDIT",
            "class_name": "Edit",
            "visible": True,
            "client_bounds_screen": (150, 150, 250, 180),
        },
        {
            "handle": 12,
            "title": "PRIVATE_COMBO_OUTSIDE",
            "class_name": "ComboBox",
            "visible": True,
            "client_bounds_screen": (600, 600, 700, 640),
        },
    )

    def uia(control_type, bounds, *, visible=True):
        left, top, right, bottom = bounds
        rectangle = SimpleNamespace(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            width=lambda: right - left,
            height=lambda: bottom - top,
        )
        return SimpleNamespace(
            element_info=SimpleNamespace(
                control_type=control_type,
                visible=visible,
            ),
            rectangle=lambda: rectangle,
        )

    descendants = (
        uia("Pane", (140, 140, 260, 190)),
        uia("Custom", (600, 600, 700, 640)),
        uia("Text", (0, 0, 20, 20), visible=False),
        uia("Button", (0, 0, 0, 0)),
    )
    result = _uia_native_field_geometry_correlation_census(
        descendants,
        provider=WindowHubUIAutomationProvider(),
        native_windows=native_windows,
        exact_active_document_windows=(document,),
    )

    assert result["available"] is True
    assert result["uia_descendant_count"] == 4
    assert result["uia_nodes_with_positive_bounds_count"] == 3
    assert result["visible_uia_nodes_with_positive_bounds_count"] == 2
    assert result["native_visible_field_like_control_count"] == 2
    assert result["document_context_native_field_like_control_count"] == 1
    assert result["visible_uia_nodes_intersecting_native_field_count"] == 2
    assert result["visible_uia_nodes_containing_native_field_center_count"] == 2
    assert result["visible_uia_nodes_edge_aligned_native_field_count"] == 1
    assert result["visible_uia_nodes_containing_document_context_field_center_count"] == 1
    assert result["visible_uia_nodes_edge_aligned_document_context_field_count"] == 0
    assert result["native_field_centers_contained_by_visible_uia_bounds_count"] == 2
    assert result["document_context_field_centers_contained_by_visible_uia_bounds_count"] == 1
    assert result["by_uia_control_type"]["pane"]["visible_bounds_containing_document_context_field_center_count"] == 1
    assert result["by_uia_control_type"]["custom"]["visible_bounds_edge_aligned_native_field_count"] == 1
    rendered = repr(result)
    for private_value in (
        "PRIVATE_DOCUMENT",
        "PRIVATE_EDIT",
        "PRIVATE_COMBO_OUTSIDE",
        "11",
        "12",
        "50",
        "(150, 150",
        "600",
    ):
        assert private_value not in rendered
    assert "handle" not in rendered.casefold()


def test_uia_native_field_geometry_correlation_fails_closed_without_snapshot():
    from tools.diagnose_windowhub_field_scope import (
        _uia_native_field_geometry_correlation_census,
    )

    result = _uia_native_field_geometry_correlation_census(
        (),
        provider=WindowHubUIAutomationProvider(),
        native_windows=None,
    )
    assert result["available"] is False
    assert result["uia_descendant_count"] == 0
    assert result["native_visible_field_like_control_count"] == 0
    assert result["document_context_native_field_like_control_count"] == 0


def test_uia_native_document_control_correlation_links_nonstandard_nodes_by_handle(monkeypatch):
    parent_chains = {
        11: (11, 50, 100),
        12: (12, 100),
        13: (13, 50, 100),
    }
    monkeypatch.setattr(
        "tools.diagnose_windowhub_field_scope._native_parent_chain",
        lambda handle: parent_chains.get(handle),
    )

    document = {
        "handle": 50,
        "title": "PRIVATE_ACTIVE_DOCUMENT",
        "class_name": "Afx:MDIChild",
        "visible": True,
        "client_bounds_screen": (100, 200, 400, 500),
    }
    native_windows = (
        {
            "handle": 11,
            "title": "PRIVATE_EDIT",
            "class_name": "Edit",
            "visible": True,
            "client_bounds_screen": (120, 220, 200, 250),
        },
        {
            "handle": 12,
            "title": "PRIVATE_COMBO_OUTSIDE",
            "class_name": "ComboBox",
            "visible": True,
            "client_bounds_screen": (500, 510, 600, 540),
        },
        {
            "handle": 13,
            "title": "PRIVATE_HIDDEN_COMBO",
            "class_name": "ComboBox",
            "visible": False,
            "client_bounds_screen": (130, 260, 190, 285),
        },
        document,
    )

    def uia(control_type, handle, *, visible=True):
        return SimpleNamespace(
            element_info=SimpleNamespace(
                control_type=control_type,
                handle=handle,
                visible=visible,
            )
        )

    descendants = (
        uia("Pane", 11),
        uia("Custom", 12),
        uia("ComboBox", 13),
        uia("Edit", 99),
        uia("Pane", 50),
    )
    result = _uia_native_document_control_correlation_census(
        descendants,
        provider=WindowHubUIAutomationProvider(),
        native_windows=native_windows,
        exact_active_document_windows=(document,),
        observed_root_handle=100,
    )

    assert result["available"] is True
    assert result["uia_descendant_count"] == 5
    assert result["uia_nodes_with_native_handle_count"] == 5
    assert result["uia_nodes_matching_native_descendant_count"] == 4
    assert result["uia_nodes_matching_native_field_like_count"] == 3
    assert result["uia_nodes_matching_visible_native_field_like_count"] == 2
    assert result["document_window_identity_available"] is True
    assert result["document_client_bounds_available"] is True
    assert result["matched_field_like_parent_chain_checked_count"] == 2
    assert result["matched_field_like_parent_chain_contains_document_count"] == 1
    assert result["matched_field_like_bounds_intersect_document_client_count"] == 1
    assert result["matched_field_like_bounds_fully_within_document_client_count"] == 1
    assert result["matched_field_like_parent_and_bounds_match_count"] == 1

    assert result["by_uia_control_type"]["pane"]["matched_native_field_like_count"] == 1
    assert result["by_uia_control_type"]["pane"]["matched_native_field_like_parent_and_bounds_match_count"] == 1
    assert result["by_uia_control_type"]["custom"]["matched_native_field_like_count"] == 1
    assert result["by_uia_control_type"]["custom"]["matched_native_field_like_parent_chain_contains_document_count"] == 0
    assert result["by_uia_control_type"]["combobox"]["matched_native_field_like_count"] == 1
    assert result["by_uia_control_type"]["combobox"]["matched_native_field_like_visible_count"] == 0

    rendered = repr(result)
    for private_value in (
        "PRIVATE_ACTIVE_DOCUMENT",
        "PRIVATE_EDIT",
        "PRIVATE_COMBO_OUTSIDE",
        "PRIVATE_HIDDEN_COMBO",
        "(120, 220",
        "11",
        "50",
        "500",
    ):
        assert private_value.casefold() not in rendered.casefold()


def test_uia_native_document_control_correlation_fails_closed_without_native_snapshot():
    descendant = SimpleNamespace(
        element_info=SimpleNamespace(
            control_type="Pane",
            handle=12345,
            visible=True,
            name="PRIVATE_NAME",
        )
    )
    result = _uia_native_document_control_correlation_census(
        (descendant,),
        provider=WindowHubUIAutomationProvider(),
        native_windows=None,
        exact_active_document_windows=(),
        observed_root_handle=999,
    )
    assert result["available"] is False
    assert result["uia_descendant_count"] == 1
    assert result["uia_nodes_matching_native_descendant_count"] == 0
    assert result["document_window_identity_available"] is False
    assert "PRIVATE_NAME" not in repr(result)
    assert "12345" not in repr(result)
    assert "999" not in repr(result)

