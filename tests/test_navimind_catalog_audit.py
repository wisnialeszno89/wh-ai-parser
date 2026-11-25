"""No false claims of catalogue enumeration or selection from a UIA field."""
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.navimind_catalog_audit import audit_catalogue_scene


def scene(title, *elements, app="Okna.exe"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=app, active_window_title=title,
            ),
        ),
        elements=tuple(elements),
    )


def ui(kind, label, aid, rid, value=None, *, enabled=True):
    return ScreenElement(
        kind=kind, label=label, metadata={
            "source": "windows_ui_automation",
            "uia_runtime_id": rid,
            "uia_visible": True, "uia_enabled": enabled,
            "uia_control_type": kind, "automation_id": aid,
            "current_value": value,
            "current_value_source": "get_value" if value else None,
        },
    )


def fields(report):
    return {field.field_name: field for field in report.fields}


def test_profile_field_can_be_found_but_catalogue_never_assumed_readable():
    report = audit_catalogue_scene(
        scene("Podstawowe parametry okna",
              ui("combobox", "Wybierz kolor profili", "1054",
                 "profile-color", "Antracyt")),
    )
    profile_color = fields(report)["profile_color"]
    assert report.safe_observation
    assert profile_color.state == "control_identified"
    assert profile_color.native_value_available
    assert profile_color.unique_runtime_id
    assert not profile_color.option_inventory_verified
    assert not profile_color.selection_roundtrip_verified
    assert fields(report)["profile_system_picker"].state == "missing_or_ambiguous"
    safe = str(report.safe_summary())
    assert "Antracyt" not in safe
    assert "profile-color" not in safe
    assert not report.safe_summary()["database_queried"]


def test_glazing_fields_do_not_inherit_values_from_other_wizard():
    report = audit_catalogue_scene(
        scene("Parametry szklenia",
              ui("combobox", "Wybierz typ pakietu szybowego",
                 "1033", "glass-1", "4/16/4"),
              ui("combobox", "Kolor ramki dystansowej",
                 "1034", "color-1", "czarny")),
    )
    assert set(fields(report)) == {
        "glazing_package", "glazing_details",
        "spacer_frame", "spacer_frame_color",
    }
    assert fields(report)["glazing_package"].native_value_available
    assert "4/16/4" not in str(report.safe_summary())


def test_duplicate_runtime_identity_blocks_control_proof():
    report = audit_catalogue_scene(
        scene("Parametry okuć",
              ui("combobox", "Wybierz profil", "1012", "duplicate"),
              ui("combobox", "Wybierz grupę", "1013", "duplicate")),
    )
    assert fields(report)["hardware_profile"].state == "present_not_verified"
    assert not fields(report)["hardware_group"].unique_runtime_id


def test_absent_or_wrong_application_fails_closed():
    report = audit_catalogue_scene(scene("Parametry okuć", app="notepad.exe"))
    assert not report.safe_observation
    assert report.fields == ()
    assert not report.safe_summary()["catalogue_selection_executed"]


def test_ambiguous_color_field_is_never_one_selected_option():
    report = audit_catalogue_scene(
        scene("Podstawowe parametry okna",
              ui("combobox", "Wybierz kolor profili", "1054", "one"),
              ui("combobox", "Wybierz kolor profili", "1054", "two")),
    )
    assert fields(report)["profile_color"].state == "missing_or_ambiguous"
    assert not fields(report)["profile_color"].native_value_available
