"""Offline read-only audits; names, values and real input stay private."""
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.navimind_catalogue_readiness import (
    inspect_catalogue_scene, summarize_catalogue_readiness,
)


def scene(title, *controls, application="Okna.exe"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=application, active_window_title=title,
            ),
        ),
        elements=controls,
    )


def combobox(name, automation_id, *, value="Sekret firmy OEM A",
             runtime_id="uia:123", enabled=True):
    return ScreenElement(
        kind="combobox", label=name,
        metadata={
            "source": "windowhub_ui_automation",
            "uia_visible": True, "uia_enabled": enabled,
            "uia_runtime_id": runtime_id,
            "automation_id": automation_id,
            "current_value": value,
            "current_value_source": "selected_text",
        },
    )


def test_basic_profile_color_and_reinforcement_are_mapped_but_not_auto_selectable():
    audit = inspect_catalogue_scene(scene(
        "Podstawowe parametry okna",
        combobox("Wybierz kolor profili", "1054"),
        combobox("Wybierz kategorię wzmocnienia", "1831", value="STD"),
    ))
    fields = {x.field_name: x for x in audit.controls}
    assert audit.stage == "basic_parameters"
    assert fields["profile_color"].state == "mapped_native_unique"
    assert fields["profile_color"].native_value_readable
    assert fields["profile_system_picker"].state == "not_found"
    assert not fields["profile_color"].safe_to_select
    assert not fields["profile_color"].choice_items_independently_observed
    report = summarize_catalogue_readiness(audit)
    assert "CURRENT_SELECTION_READABLE=2" in report
    assert "CATALOGUE_SELECTION_EXECUTABLE=False" in report
    assert "Sekret firmy OEM A" not in report
    assert "uia:123" not in report


def test_glazing_dropdowns_have_separate_ids_and_do_not_claim_catalogue_enumeration():
    audit = inspect_catalogue_scene(scene(
        "Parametry szklenia",
        combobox("Wybierz typ pakietu szybowego", "1033", value="Pakiet X"),
        combobox("Ramka dystansowa", "1035", value="Ramka Y", runtime_id="uia:456"),
        combobox("Kolor ramki dystansowej", "1034", value="Kolor Z", runtime_id="uia:789"),
    ))
    assert audit.stage == "glazing"
    assert sum(x.native_value_readable for x in audit.controls) == 3
    assert not audit.selection_verified
    assert all(not x.safe_to_select for x in audit.controls)
    assert all(not x.choice_items_independently_observed for x in audit.controls)


def test_hardware_controls_are_not_confused_with_profile_color_reused_automation_id():
    audit = inspect_catalogue_scene(scene(
        "Parametry okuć",
        combobox("Wybierz profil", "1012"),
        combobox("Wybierz grupę", "1013", runtime_id="uia:2"),
        combobox("Wybierz kolor", "1054", runtime_id="uia:3"),
    ))
    assert audit.stage == "hardware"
    assert {x.field_name for x in audit.controls if x.native_value_readable} == {
        "hardware_profile", "hardware_group", "hardware_inner_color",
    }


def test_duplicate_or_disabled_control_is_not_verified_catalogue_selector():
    duplicate = combobox("Wybierz kolor profili", "1054", runtime_id="uia:other")
    audit = inspect_catalogue_scene(scene(
        "Podstawowe parametry okna",
        combobox("Wybierz kolor profili", "1054"), duplicate,
        combobox("Wybierz kategorię wzmocnienia", "1831", enabled=False),
    ))
    fields = {x.field_name: x for x in audit.controls}
    assert fields["profile_color"].state == "ambiguous"
    assert fields["reinforcement_category"].state == "mapped_but_native_identity_unverified"
    assert not fields["reinforcement_category"].safe_to_select


def test_foreground_app_and_step_must_be_known():
    assert inspect_catalogue_scene(scene(
        "Podstawowe parametry okna",
        combobox("Wybierz kolor profili", "1054"),
        application="Notepad.exe",
    )).status == "catalogue_wizard_not_foreground"
    assert inspect_catalogue_scene(scene("Okna - Start1")).controls == ()


def test_local_list_peek_never_attributed_to_one_catalogue_without_owner_proof():
    from app.agent.runtime.navimind_catalogue_readiness import (
        visible_unattributed_catalogue_items,
    )
    from tools.inspect_navimind_catalogues_live import run_probe
    item = ScreenElement(
        kind="listitem", label="Sensitive producer article",
        metadata={
            "source": "windowhub_ui_automation",
            "uia_visible": True, "uia_enabled": True,
            "uia_runtime_id": "list-row-1",
        },
    )
    current = scene(
        "Podstawowe parametry okna",
        combobox("Wybierz kolor profili", "1054"), item,
    )
    assert visible_unattributed_catalogue_items(current) == 1
    assert visible_unattributed_catalogue_items(
        current, include_labels=True,
    ) == ("Sensitive producer article",)
    safe = run_probe(observe=lambda: current)
    assert safe["visible_unattributed_items"] == 1
    assert safe["options_owned_by_specific_field"] is False
    assert "Sensitive producer article" not in repr(safe)
    local_only = run_probe(
        observe=lambda: current, show_local_options=True,
    )
    assert local_only["unattributed_local_option_labels"] == [
        "Sensitive producer article"
    ]
    assert not local_only["input_performed"]
    assert not local_only["data_sent_to_cloud"]


def test_unrelated_window_cannot_dump_list_item_labels():
    from app.agent.runtime.navimind_catalogue_readiness import (
        visible_unattributed_catalogue_items,
    )
    from tools.inspect_navimind_catalogues_live import run_probe
    item = ScreenElement(
        kind="listitem", label="Private client name",
        metadata={
            "source": "windows_ui_automation",
            "uia_visible": True, "uia_enabled": True,
            "uia_runtime_id": "secret-row",
        },
    )
    wrong_app = scene(
        "Podstawowe parametry okna", item, application="Notepad.exe",
    )
    assert visible_unattributed_catalogue_items(
        wrong_app, include_labels=True,
    ) == ()
    assert "Private client name" not in repr(
        run_probe(observe=lambda: wrong_app, show_local_options=True)
    )


def test_native_expand_pattern_discovery_does_not_grant_catalogue_selection():
    from app.agent.perception.windowhub_ui_automation_provider import (
        WindowHubUIAutomationProvider,
    )
    from types import SimpleNamespace
    exposed = SimpleNamespace(
        iface_expand_collapse=object(),
        iface_selection_item=None, iface_selection=None, iface_value=object(),
    )
    patterns = WindowHubUIAutomationProvider._native_pattern_support(
        exposed, "combobox"
    )
    assert patterns["expand_collapse"] is True
    assert patterns["selection_item"] is False
    assert patterns["value"] is True
    assert WindowHubUIAutomationProvider._native_pattern_support(
        exposed, "button"
    ) == {}
    field = ScreenElement(
        kind="combobox", label="Wybierz kolor profili",
        metadata={
            "source": "windowhub_ui_automation",
            "uia_visible": True, "uia_enabled": True,
            "uia_runtime_id": "native:combo",
            "automation_id": "1054",
            "current_value": "BIAŁY", "current_value_source": "selected_text",
            "uia_native_pattern_support": patterns,
        },
    )
    audit = inspect_catalogue_scene(scene("Podstawowe parametry okna", field))
    color = next(x for x in audit.controls if x.field_name == "profile_color")
    assert color.native_expand_pattern_available
    assert not color.native_selection_pattern_available
    assert not color.safe_to_select
    result = summarize_catalogue_readiness(audit)
    assert "NATIVE_EXPAND_PATTERN=1" in result
    assert "CATALOGUE_SELECTION_EXECUTABLE=False" in result
