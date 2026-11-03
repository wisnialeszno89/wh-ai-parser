from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.offers.windowhub_offer_form_map import (
    WindowHubFormStep,
    WindowHubOfferFormMap,
    identify_windowhub_form_step,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def _element(
    kind,
    label,
    automation_id,
    *,
    runtime_id="1",
    source="windows_ui_automation",
    visible=True,
    enabled=True,
):
    return ScreenElement(
        kind=kind,
        label=label,
        metadata={
            "source": source,
            "automation_id": automation_id,
            "uia_control_type": kind,
            "uia_runtime_id": runtime_id,
            "uia_visible": visible,
            "uia_enabled": enabled,
        },
    )


def _scene(title, elements, *, application="Okna.exe"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=application,
                active_window_title=title,
            )
        ),
        elements=tuple(elements),
    )


def test_identifies_windowhub_wizard_steps_with_polish_diacritics():
    assert identify_windowhub_form_step("Wielkość okna") == WindowHubFormStep.DIMENSIONS
    assert identify_windowhub_form_step("Podstawowe parametry okna") == WindowHubFormStep.BASIC_PARAMETERS
    assert identify_windowhub_form_step("Parametry szklenia") == WindowHubFormStep.GLAZING
    assert identify_windowhub_form_step("Parametry parapetu") == WindowHubFormStep.SILL
    assert identify_windowhub_form_step("Parametry okuć") == WindowHubFormStep.HARDWARE
    assert identify_windowhub_form_step("Unknown dialog") is None


def test_maps_repeated_width_and_height_labels_by_step_and_automation_id():
    scene = _scene(
        "Wielkość okna",
        (
            _element("edit", "Szerokość", "1000", runtime_id="w1"),
            _element("edit", "Wysokość", "1001", runtime_id="h1"),
            _element("edit", "Szerokość", "1014", runtime_id="w2"),
            _element("edit", "Wysokość", "1015", runtime_id="h2"),
            _element("edit", "Szerokość", "1022", runtime_id="w3"),
            _element("edit", "Wysokość", "1023", runtime_id="h3"),
            _element("edit", "Szerokość", "1026", runtime_id="w4"),
            _element("edit", "Wysokość", "1027", runtime_id="h4"),
            _element("edit", "Szerokość", "1024", runtime_id="w5"),
            _element("edit", "Wysokość", "1025", runtime_id="h5"),
        ),
    )

    snapshot = WindowHubOfferFormMap().inspect(scene)

    assert snapshot is not None
    assert snapshot.step == WindowHubFormStep.DIMENSIONS
    assert len(snapshot.fields) == 10
    assert all(match.is_unique for match in snapshot.fields)
    assert snapshot.field("width_1").element.metadata["automation_id"] == "1000"
    assert snapshot.field("height_5").element.metadata["automation_id"] == "1025"


def test_same_automation_id_maps_to_different_fields_on_different_steps():
    mapper = WindowHubOfferFormMap()

    basic = mapper.inspect(
        _scene(
            "Podstawowe parametry okna",
            (_element("combobox", "Wybierz kolor profili", "1054"),),
        )
    )
    sill = mapper.inspect(
        _scene(
            "Parametry parapetu",
            (_element("combobox", "Wybierz kolor", "1054"),),
        )
    )

    assert basic.field("profile_color").is_unique
    assert sill.field("sill_color").is_unique
    assert basic.field("profile_color").element is not sill.field("sill_color").element


def test_reused_edit_automation_id_is_disambiguated_by_semantic_label():
    scene = _scene(
        "Dodawanie nowej pozycji",
        (
            _element("edit", "Ile sztuk", "1001", runtime_id="quantity"),
            _element("edit", "Opis pozycji", "1001", runtime_id="description"),
        ),
    )

    snapshot = WindowHubOfferFormMap().inspect(scene)

    assert snapshot.field("quantity_input").is_unique
    assert snapshot.field("description_input").is_unique
    assert (
        snapshot.field("quantity_input").element.metadata["uia_runtime_id"]
        == "quantity"
    )
    assert (
        snapshot.field("description_input").element.metadata["uia_runtime_id"]
        == "description"
    )


def test_ambiguous_duplicate_uia_matches_are_not_resolved():
    scene = _scene(
        "Wielkość okna",
        (
            _element("edit", "Szerokość", "1000", runtime_id="width-a"),
            _element("edit", "Szerokość", "1000", runtime_id="width-b"),
        ),
    )

    match = WindowHubOfferFormMap().resolve(scene, "width_1")

    assert match.status == "ambiguous"
    assert match.candidate_count == 2
    assert match.element is None
    assert not match.is_unique


def test_ignores_ocr_hidden_and_non_windowhub_controls():
    scene = _scene(
        "Wielkość okna",
        (
            _element(
                "edit",
                "Szerokość",
                "1000",
                runtime_id="ocr",
                source="windows_ocr",
            ),
            _element(
                "edit",
                "Szerokość",
                "1000",
                runtime_id="hidden",
                visible=False,
            ),
            _element(
                "edit",
                "Szerokość",
                "1000",
                runtime_id="visible-uia",
            ),
        ),
    )

    match = WindowHubOfferFormMap().resolve(scene, "width_1")

    assert match.is_unique
    assert match.element.metadata["uia_runtime_id"] == "visible-uia"


def test_does_not_map_other_applications_or_unknown_dialogs():
    mapper = WindowHubOfferFormMap()

    other_app = mapper.inspect(
        _scene(
            "Wielkość okna",
            (_element("edit", "Szerokość", "1000"),),
            application="Code.exe",
        )
    )
    unknown_dialog = mapper.inspect(
        _scene(
            "Klient",
            (_element("edit", "Szerokość", "1000"),),
        )
    )

    assert other_app is None
    assert unknown_dialog is None


def test_maps_known_hardware_fields_but_keeps_disabled_state_visible():
    scene = _scene(
        "Parametry okuć",
        (
            _element("combobox", "Wybierz profil", "1012"),
            _element("combobox", "Wybierz grupę", "1013"),
            _element("combobox", "Wybierz kolor", "1054", enabled=False),
            _element("combobox", "Wybierz kolor zewnętrzny", "1545"),
        ),
    )

    snapshot = WindowHubOfferFormMap().inspect(scene)

    assert snapshot.field("hardware_profile").is_unique
    assert snapshot.field("hardware_group").is_unique
    assert snapshot.field("hardware_inner_color").is_unique
    assert snapshot.field("hardware_inner_color").enabled is False
    assert snapshot.field("hardware_outer_color").is_unique
