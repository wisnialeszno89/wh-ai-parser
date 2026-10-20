from types import SimpleNamespace

from tools.diagnose_windowhub_field_scope import (
    _field_document_window_geometry,
    _native_document_window_geometry_summary,
)


def make_field(bounds):
    if bounds is None:
        x = y = width = height = None
    else:
        x, y, width, height = bounds
    return SimpleNamespace(
        label="PRIVATE_FIELD_LABEL",
        value="PRIVATE_FIELD_VALUE",
        element=SimpleNamespace(x=x, y=y, width=width, height=height),
    )


def make_document_window(*, visible=True, client_bounds_screen=(120, 180, 420, 480)):
    return {
        "handle": 987654,
        "title": "PRIVATE_ACTIVE_DOCUMENT",
        "class_name": "Afx:MDIChild",
        "visible": visible,
        "client_bounds_screen": client_bounds_screen,
    }


ROOT_RECT = SimpleNamespace(left=100, top=100)


def test_geometry_reports_field_fully_contained_without_exposing_identity_or_bounds():
    window = make_document_window()
    result = _field_document_window_geometry(
        make_field((40, 100, 100, 30)),
        exact_active_document_windows=(window,),
        root_window_rect=ROOT_RECT,
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


def test_geometry_distinguishes_partial_overlap_from_full_containment():
    result = _field_document_window_geometry(
        make_field((280, 110, 60, 30)),
        exact_active_document_windows=(make_document_window(),),
        root_window_rect=ROOT_RECT,
    )

    assert result["active_document_client_geometry_available"] is True
    assert result["field_bounds_fully_within_active_document_client_area"] is False
    assert result["field_bounds_intersect_active_document_client_area"] is True


def test_geometry_marks_nonoverlapping_field_as_outside_active_document_area():
    result = _field_document_window_geometry(
        make_field((400, 120, 40, 20)),
        exact_active_document_windows=(make_document_window(),),
        root_window_rect=ROOT_RECT,
    )

    assert result["active_document_client_geometry_available"] is True
    assert result["field_bounds_fully_within_active_document_client_area"] is False
    assert result["field_bounds_intersect_active_document_client_area"] is False


def test_geometry_stays_unknown_without_one_unique_visible_window_and_valid_bounds():
    duplicate_match = _field_document_window_geometry(
        make_field((40, 100, 100, 30)),
        exact_active_document_windows=(
            make_document_window(),
            make_document_window(),
        ),
        root_window_rect=ROOT_RECT,
    )
    hidden_window = _field_document_window_geometry(
        make_field((40, 100, 100, 30)),
        exact_active_document_windows=(make_document_window(visible=False),),
        root_window_rect=ROOT_RECT,
    )
    missing_rect = _field_document_window_geometry(
        make_field((40, 100, 100, 30)),
        exact_active_document_windows=(
            make_document_window(client_bounds_screen=None),
        ),
        root_window_rect=ROOT_RECT,
    )
    missing_field_bounds = _field_document_window_geometry(
        make_field(None),
        exact_active_document_windows=(make_document_window(),),
        root_window_rect=ROOT_RECT,
    )

    for result in (duplicate_match, hidden_window, missing_rect, missing_field_bounds):
        assert result == {
            "active_document_client_geometry_available": False,
            "field_bounds_fully_within_active_document_client_area": None,
            "field_bounds_intersect_active_document_client_area": None,
        }


def test_geometry_summary_emits_counts_only():
    result = _native_document_window_geometry_summary((
        make_document_window(),
        make_document_window(visible=False, client_bounds_screen=None),
    ))

    assert result == {
        "exact_title_match_count": 2,
        "visible_exact_title_match_count": 1,
        "client_bounds_available_exact_title_match_count": 1,
    }
    rendered = repr(result)
    assert "PRIVATE_ACTIVE_DOCUMENT" not in rendered
    assert "987654" not in rendered
