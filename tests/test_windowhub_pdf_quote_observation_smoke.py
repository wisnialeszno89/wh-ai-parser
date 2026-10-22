from __future__ import annotations

from types import SimpleNamespace

from tools.smoke_windowhub_pdf_quote_observation import build_report


def make_element(kind, label, **metadata):
    return SimpleNamespace(kind=kind, label=label, metadata=metadata)


def make_scene(elements, *, title="WindowHub - Oferta", active_document="Oferta robocza"):
    observation = SimpleNamespace(
        state=SimpleNamespace(
            active_application="WindowsDesktop",
            active_window_title=title,
        ),
        metadata={"window_focused": True},
    )
    return SimpleNamespace(
        observation=observation,
        elements=tuple(elements),
        metadata={
            "active_document": active_document,
            "active_document_resolution": "resolved" if active_document else "unresolved",
            "document_tab_count": 1 if active_document else 0,
            "selected_document_tab_count": 1 if active_document else 0,
        },
        active_document=active_document,
    )


def test_read_only_probe_reports_quote_fields_and_scoped_writes():
    scene = make_scene([
        make_element(
            "edit", "Ilość", current_value="2 szt.", uia_enabled=True,
            uia_selected=None, document_scope="Oferta robocza",
        ),
        make_element(
            "edit", "Szerokość", current_value="1200", uia_enabled=True,
            uia_selected=None, document_scope="Oferta robocza",
        ),
        make_element(
            "edit", "Wysokość", current_value="1500", uia_enabled=True,
            uia_selected=None, document_scope="Oferta robocza",
        ),
        make_element(
            "list_item", "Okno", uia_selected=True,
            document_scope="Oferta robocza",
        ),
        make_element("button", "Zapisz szkic", uia_enabled=True),
    ])

    report = build_report(scene)

    assert report["read_only"] is True
    assert report["desktop_actions_executed"] == 0
    assert report["network_calls"] == 0
    assert report["windowhub_title_match"] is True
    assert report["basic_quote_field_roles_missing_on_current_screen"] == []
    assert report["all_observed_text_fields_have_write_scope"] is True
    assert {item["field"] for item in report["quote_field_candidates"]} == {
        "quantity", "width", "height",
    }
    assert any(
        item["role"] == "product_choice" and item["selected"] is True
        for item in report["workflow_control_candidates"]
    )


def test_read_only_probe_redacts_unexpected_text_in_numeric_quote_fields():
    scene = make_scene([
        make_element(
            "edit", "Szerokość", current_value="Customer: Jan Kowalski",
            uia_enabled=True,
        ),
        make_element(
            "edit", "Kod klienta", current_value="CLIENT-12345",
            uia_enabled=True,
        ),
    ])

    report = build_report(scene)

    width = next(
        item for item in report["quote_field_candidates"]
        if item["field"] == "width"
    )
    serialized = str(report)
    assert width["value_redacted"] is True
    assert "Jan Kowalski" not in serialized
    assert "CLIENT-12345" not in serialized
    assert report["all_observed_text_fields_have_write_scope"] is False


def test_read_only_probe_does_not_claim_full_workflow_when_controls_are_on_other_screen():
    scene = make_scene([
        make_element("button", "Nowa oferta", uia_enabled=True),
    ])

    report = build_report(scene)

    assert report["windowhub_title_match"] is True
    assert report["basic_quote_field_roles_seen"] == []
    assert set(report["basic_quote_field_roles_missing_on_current_screen"]) == {
        "product_type", "quantity", "width", "height",
    }
    assert "offer editor screen" in report["recommended_next_step"]


def test_read_only_probe_flags_unmatched_foreground_application():
    scene = make_scene(
        [make_element("edit", "Szerokość", current_value="1200", uia_enabled=True)],
        title="Notepad",
    )

    report = build_report(scene)

    assert report["windowhub_title_match"] is False
    assert "Activate the WindowHub" in report["recommended_next_step"]
