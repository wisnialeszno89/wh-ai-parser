from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from tools.diagnose_windowhub_semantics import (
    _normalize_process_name,
    _parse_window_handle,
    _select_target_window,
    build_read_only_report,
)


def make_scene():
    return SimpleNamespace(
        active_document=None,
        metadata={
            "active_document_resolution": "not_observed",
            "document_tab_count": 0,
            "selected_document_tab_count": 0,
        },
        elements=(
            SimpleNamespace(
                label="Szerokość",
                kind="edit",
                interaction_capability="clickable",
                metadata={
                    "uia_enabled": True,
                    "uia_visible": True,
                    "uia_selected": None,
                    "current_value": "1200",
                    "document_scope": None,
                    "provider_element_id": "uia:secret-runtime-id",
                    "window_handle": 123456,
                },
            ),
            SimpleNamespace(
                label="Okno",
                kind="listitem",
                interaction_capability="clickable",
                metadata={
                    "uia_enabled": True,
                    "uia_visible": True,
                    "uia_selected": True,
                    "current_value": None,
                    "uia_owned_modal": True,
                },
            ),
        ),
    )


def test_read_only_report_redacts_values_window_title_and_scope_by_default():
    report = build_read_only_report(
        make_scene(),
        active_window_title="WindowHub - Klient Kowalski",
        window_focused=True,
    )

    serialized = json.dumps(report, ensure_ascii=False)

    assert report["mode"] == "READ_ONLY"
    assert report["computer_actions_executed"] is False
    assert report["network_calls_made"] is False
    assert report["files_written"] is False
    assert report["screenshot_saved"] is False
    assert report["active_window"]["title_contains_windowhub"] is True
    assert report["active_window"]["title"] == "<redacted>"
    assert report["active_document"]["resolved"] is False
    assert report["inventory"]["elements_with_document_scope"] == 0
    assert report["elements"][0]["label"] == "Szerokość"
    assert report["elements"][0]["current_value_available"] is True
    assert report["elements"][0]["current_value_nonempty"] is True
    assert report["elements"][0]["document_scope_status"] == "unknown"
    assert report["elements"][1]["selected"] is True
    assert "1200" not in serialized
    assert "Klient Kowalski" not in serialized
    assert "secret-runtime-id" not in serialized
    assert "123456" not in serialized


def test_read_only_report_can_explicitly_include_sensitive_diagnostics():
    report = build_read_only_report(
        make_scene(),
        active_window_title="WindowHub - Klient Kowalski",
        window_focused=True,
        include_sensitive_values=True,
    )

    assert report["active_window"]["title"] == "WindowHub - Klient Kowalski"
    assert report["elements"][0]["current_value"] == "1200"
    assert report["elements"][0]["document_scope"] is None


def test_read_only_report_marks_document_scope_relationships():
    scene = SimpleNamespace(
        active_document="Oferta robocza",
        metadata={"active_document_resolution": "resolved"},
        elements=(
            SimpleNamespace(
                label="Szerokość",
                kind="edit",
                interaction_capability="clickable",
                metadata={"document_scope": "Oferta robocza"},
            ),
            SimpleNamespace(
                label="Szerokość",
                kind="edit",
                interaction_capability="clickable",
                metadata={"document_scope": "Inna oferta"},
            ),
            SimpleNamespace(
                label="Wysokość",
                kind="edit",
                interaction_capability="clickable",
                metadata={},
            ),
        ),
    )

    report = build_read_only_report(
        scene,
        active_window_title="WindowHub",
        window_focused=True,
    )

    assert [item["document_scope_status"] for item in report["elements"]] == [
        "active_document",
        "other_document",
        "unknown",
    ]
    assert report["active_document"]["resolved"] is True
    assert report["active_document"]["name"] == "<redacted>"


def test_read_only_report_caps_inventory_and_marks_truncation():
    scene = SimpleNamespace(
        active_document=None,
        metadata={},
        elements=tuple(
            SimpleNamespace(
                label=f"Button {index}",
                kind="button",
                interaction_capability="clickable",
                metadata={},
            )
            for index in range(5)
        ),
    )

    report = build_read_only_report(
        scene,
        active_window_title="WindowHub",
        window_focused=True,
        max_elements=2,
    )

    assert report["inventory"]["element_count"] == 5
    assert report["inventory"]["elements_reported"] == 2
    assert report["inventory"]["truncated"] is True
    assert [item["label"] for item in report["elements"]] == [
        "Button 0",
        "Button 1",
    ]


@pytest.mark.parametrize("limit", (0, -1, 501, True))
def test_read_only_report_rejects_invalid_element_limit(limit):
    with pytest.raises(ValueError, match="between 1 and 500"):
        build_read_only_report(
            make_scene(),
            active_window_title="WindowHub",
            window_focused=True,
            max_elements=limit,
        )



def make_window(
    title,
    handle,
    *,
    left=10,
    top=20,
    width=900,
    height=700,
    minimized=False,
    visible=True,
):
    return SimpleNamespace(
        title=title,
        _hWnd=handle,
        left=left,
        top=top,
        width=width,
        height=height,
        isMinimized=minimized,
        visible=visible,
    )


def test_window_selector_finds_windowhub_when_powershell_is_foreground():
    powershell = make_window("Windows PowerShell", 100)
    windowhub = make_window("WindowHub - Oferta", 200)

    selected, stop_reason = _select_target_window(
        (powershell, windowhub),
        title_contains="WindowHub",
    )

    assert selected is windowhub
    assert stop_reason is None


def test_window_selector_fails_closed_when_multiple_visible_windows_match():
    main_window = make_window("WindowHub - Oferta", 200)
    second_window = make_window("WindowHub - Ustawienia", 201)

    selected, stop_reason = _select_target_window(
        (main_window, second_window),
        title_contains="WindowHub",
    )

    assert selected is None
    assert stop_reason is not None
    assert "2 visible top-level windows" in stop_reason
    assert "ambiguous target" in stop_reason


def test_window_selector_skips_minimized_and_invisible_matches():
    minimized = make_window("WindowHub - Stare", 200, minimized=True)
    invisible = make_window("WindowHub - Ukryte", 201, visible=False)
    visible = make_window("WindowHub - Oferta", 202)

    selected, stop_reason = _select_target_window(
        (minimized, invisible, visible),
        title_contains="WindowHub",
    )

    assert selected is visible
    assert stop_reason is None


def test_window_selector_supports_a_custom_unique_title_fragment():
    other = make_window("Notepad", 100)
    target = make_window("WH - Oferta", 200)

    selected, stop_reason = _select_target_window(
        (other, target),
        title_contains="WH -",
    )

    assert selected is target
    assert stop_reason is None


def test_window_selector_reports_no_match_without_exposing_other_window_title():
    selected, stop_reason = _select_target_window(
        (make_window("Windows PowerShell - customer secret", 100),),
        title_contains="WindowHub",
    )

    assert selected is None
    assert stop_reason is not None
    assert "No visible" in stop_reason
    assert "customer secret" not in stop_reason


def test_report_can_match_custom_selector_without_claiming_windowhub_literal():
    report = build_read_only_report(
        make_scene(),
        active_window_title="WH - Oferta",
        window_focused=False,
        window_title_contains="WH -",
    )

    assert report["active_window"]["title_matches_selector"] is True
    assert report["active_window"]["title_contains_windowhub"] is False
    assert report["active_window"]["focused"] is False



def test_process_name_selector_finds_application_when_title_has_no_product_name():
    unrelated = make_window("Unrelated document", 100)
    target = make_window("Oferta - klient", 200)
    process_names = {100: "Code", 200: "Okna.exe"}

    selected, stop_reason = _select_target_window(
        (unrelated, target),
        process_name="Okna",
        process_name_checker=lambda handle: process_names.get(handle),
    )

    assert selected is target
    assert stop_reason is None


def test_process_name_selector_fails_closed_when_multiple_windows_match():
    first = make_window("Oferta", 200)
    second = make_window("Konstrukcja", 201)
    process_names = {200: "Okna", 201: "OKNA.EXE"}

    selected, stop_reason = _select_target_window(
        (first, second),
        process_name="okna.exe",
        process_name_checker=lambda handle: process_names.get(handle),
    )

    assert selected is None
    assert stop_reason is not None
    assert "2 visible top-level windows" in stop_reason
    assert "ambiguous target" in stop_reason


def test_process_name_selector_does_not_fall_back_to_title_when_lookup_fails():
    target = make_window("WindowHub - Offer", 200)

    selected, stop_reason = _select_target_window(
        (target,),
        process_name="Okna",
        process_name_checker=lambda handle: None,
    )

    assert selected is None
    assert stop_reason is not None
    assert "process name 'okna'" in stop_reason


def test_process_name_selector_skips_minimized_or_invisible_windows():
    minimized = make_window("Stare", 200, minimized=True)
    invisible = make_window("Ukryte", 201, visible=False)
    visible = make_window("Oferta", 202)
    process_names = {200: "Okna", 201: "Okna", 202: "Okna"}

    selected, stop_reason = _select_target_window(
        (minimized, invisible, visible),
        process_name="Okna",
        process_name_checker=lambda handle: process_names.get(handle),
    )

    assert selected is visible
    assert stop_reason is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Okna", "okna"),
        ("Okna.exe", "okna"),
        (r"C:\Program Files\Okna\Okna.exe", "okna"),
        ("  OKNA.EXE  ", "okna"),
        ("", ""),
        (None, ""),
    ],
)
def test_process_name_normalization(raw, expected):
    assert _normalize_process_name(raw) == expected


def test_report_explains_process_name_selector_without_unredacting_window_title():
    report = build_read_only_report(
        make_scene(),
        active_window_title="Oferta - Klient Kowalski",
        window_focused=False,
        process_name="Okna.exe",
    )

    assert report["target_selection"]["mode"] == "process_name"
    assert report["target_selection"]["selector"] == "okna"
    assert report["target_selection"]["target_matched"] is True
    assert report["active_window"]["title_contains_windowhub"] is False
    assert report["active_window"]["title"] == "<redacted>"



def test_explicit_window_handle_disambiguates_process_windows():
    first = make_window("Offer", 200)
    second = make_window("Settings", 201)
    process_names = {200: "Okna", 201: "Okna.exe"}

    selected, stop_reason = _select_target_window(
        (first, second),
        process_name="Okna",
        window_handle=201,
        process_name_checker=lambda handle: process_names.get(handle),
    )

    assert selected is second
    assert stop_reason is None


def test_explicit_window_handle_never_falls_back_to_another_window_of_same_process():
    first = make_window("Offer", 200)
    second = make_window("Settings", 201)
    process_names = {200: "Okna", 201: "Okna"}

    selected, stop_reason = _select_target_window(
        (first, second),
        process_name="Okna",
        window_handle=999,
        process_name_checker=lambda handle: process_names.get(handle),
    )

    assert selected is None
    assert stop_reason is not None
    assert "window handle 0x3E7 owned by process 'okna'" in stop_reason


def test_explicit_window_handle_requires_process_identity_verification():
    with pytest.raises(ValueError, match="requires process_name"):
        _select_target_window(
            (make_window("Offer", 200),),
            window_handle=200,
        )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("200", 200),
        ("0xC8", 200),
    ],
)
def test_parse_window_handle_accepts_decimal_and_hex(raw, expected):
    assert _parse_window_handle(raw) == expected


@pytest.mark.parametrize("raw", ("0", "-1", "not-a-handle"))
def test_parse_window_handle_rejects_invalid_values(raw):
    with pytest.raises(Exception):
        _parse_window_handle(raw)


def test_report_identifies_explicit_handle_selection_without_unredacting_title():
    report = build_read_only_report(
        make_scene(),
        active_window_title="Offer - Klient Kowalski",
        window_focused=False,
        process_name="Okna.exe",
        window_handle=0x1770436,
    )

    assert report["target_selection"]["mode"] == "window_handle"
    assert report["target_selection"]["selector"] == "0x1770436"
    assert report["target_selection"]["target_matched"] is True
    assert report["active_window"]["title"] == "<redacted>"
