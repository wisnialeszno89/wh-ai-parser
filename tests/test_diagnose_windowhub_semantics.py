from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from tools.diagnose_windowhub_semantics import build_read_only_report


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
