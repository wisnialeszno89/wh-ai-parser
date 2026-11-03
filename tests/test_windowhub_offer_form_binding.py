from app.agent.agent_intent import AgentIntent
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.offers.agent_construction_compiler import AgentConstructionCompiler
from app.agent.offers.offer_context import OfferContext
from app.agent.offers.windowhub_offer_form_binding import (
    WindowHubBindingStatus,
    WindowHubOfferFormBinder,
)
from app.agent.offers.windowhub_offer_form_plan import (
    WindowHubOfferFormPlanBuilder,
)
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def _context(**overrides):
    values = {
        "raw_request": "Okno 1200x1500 DKR",
        "width": 1200,
        "height": 1500,
        "quantity": 2,
        "product_type": "window",
        "profile": "VEKA_82",
        "opening": "RIGHT_TILT_TURN",
        "glazing": "triple",
    }
    values.update(overrides)
    return OfferContext(**values)


def _plan(context=None):
    resolved_context = context or _context()
    project = AgentConstructionCompiler().compile(resolved_context)
    return WindowHubOfferFormPlanBuilder().build(resolved_context, project)


def _element(kind, label, automation_id, *, runtime_id="1", enabled=True):
    return ScreenElement(
        kind=kind,
        label=label,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "automation_id": automation_id,
            "uia_control_type": kind,
            "uia_runtime_id": runtime_id,
            "uia_visible": True,
            "uia_enabled": enabled,
        },
    )


def _scene(title, elements, *, application="Okna.exe"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=application,
                active_window_title=title,
            ),
        ),
        elements=tuple(elements),
    )


def test_binds_position_fields_to_unique_controls_for_manual_review_only():
    binding = WindowHubOfferFormBinder().bind(
        _plan(),
        _scene(
            "Dodawanie nowej pozycji",
            (
                _element("radiobutton", "Okno", "1329", runtime_id="item-type"),
                _element("edit", "Ile sztuk", "1001", runtime_id="quantity"),
            ),
        ),
    )

    assert binding.step.value == "position"
    item_type = next(
        item for item in binding.fields
        if item.field_name == "item_type_window"
    )
    quantity = next(
        item for item in binding.fields
        if item.field_name == "quantity_input"
    )

    assert item_type.status == WindowHubBindingStatus.MATCHED_FOR_REVIEW
    assert quantity.status == WindowHubBindingStatus.MATCHED_FOR_REVIEW
    assert quantity.element.metadata["uia_runtime_id"] == "quantity"
    assert binding.action_authorized is False
    assert all(item.action_authorized is False for item in binding.fields)


def test_dimension_fields_are_observed_but_remain_semantically_unverified():
    elements = []
    for label, automation_id in (
        ("Szerokość", "1000"),
        ("Wysokość", "1001"),
        ("Szerokość", "1014"),
        ("Wysokość", "1015"),
        ("Szerokość", "1022"),
        ("Wysokość", "1023"),
        ("Szerokość", "1026"),
        ("Wysokość", "1027"),
        ("Szerokość", "1024"),
        ("Wysokość", "1025"),
    ):
        elements.append(
            _element("edit", label, automation_id, runtime_id=automation_id)
        )

    binding = WindowHubOfferFormBinder().bind(
        _plan(),
        _scene("Wielkość okna", elements),
    )

    width = next(
        item for item in binding.fields
        if item.field_name == "width_1"
    )
    height = next(
        item for item in binding.fields
        if item.field_name == "height_1"
    )

    assert width.status == WindowHubBindingStatus.MAPPING_UNVERIFIED
    assert height.status == WindowHubBindingStatus.MAPPING_UNVERIFIED
    assert width.is_uniquely_observed is True
    assert height.is_uniquely_observed is True
    assert binding.action_authorized is False


def test_ambiguous_controls_are_not_selected():
    binding = WindowHubOfferFormBinder().bind(
        _plan(),
        _scene(
            "Wielkość okna",
            (
                _element("edit", "Szerokość", "1000", runtime_id="width-a"),
                _element("edit", "Szerokość", "1000", runtime_id="width-b"),
            ),
        ),
    )

    width = next(
        item for item in binding.fields
        if item.field_name == "width_1"
    )

    assert width.status == WindowHubBindingStatus.CONTROL_AMBIGUOUS
    assert width.element is None
    assert width.candidate_count == 2


def test_missing_and_disabled_controls_are_reported_separately():
    binder = WindowHubOfferFormBinder()
    plan = _plan()

    missing = binder.bind(
        plan,
        _scene("Dodawanie nowej pozycji", ()),
    )
    missing_quantity = next(
        item for item in missing.fields
        if item.field_name == "quantity_input"
    )
    assert missing_quantity.status == WindowHubBindingStatus.CONTROL_MISSING

    disabled = binder.bind(
        plan,
        _scene(
            "Dodawanie nowej pozycji",
            (_element("edit", "Ile sztuk", "1001", enabled=False),),
        ),
    )
    disabled_quantity = next(
        item for item in disabled.fields
        if item.field_name == "quantity_input"
    )
    assert disabled_quantity.status == WindowHubBindingStatus.CONTROL_DISABLED


def test_catalog_field_is_matched_but_not_authorized_for_selection():
    binding = WindowHubOfferFormBinder().bind(
        _plan(),
        _scene(
            "Parametry szklenia",
            (
                _element(
                    "combobox",
                    "Wybierz typ pakietu szybowego",
                    "1033",
                    runtime_id="glazing",
                ),
            ),
        ),
    )

    glazing = next(
        item for item in binding.fields
        if item.field_name == "glazing_package"
    )

    assert glazing.status == WindowHubBindingStatus.CATALOG_SELECTION_UNVERIFIED
    assert glazing.is_uniquely_observed is True
    assert glazing.action_authorized is False


def test_invalid_plan_blocks_all_field_binding():
    context = _context(quantity=0)
    plan = _plan(context)
    binding = WindowHubOfferFormBinder().bind(
        plan,
        _scene(
            "Dodawanie nowej pozycji",
            (_element("edit", "Ile sztuk", "1001"),),
        ),
    )

    assert binding.reason == "offer_plan_blocked"
    assert all(
        item.status == WindowHubBindingStatus.PLAN_BLOCKED
        for item in binding.fields
    )
    assert binding.action_authorized is False


def test_optional_color_mapping_without_field_name_requires_review():
    context = _context(color_inside="white", color_outside="anthracite")
    binding = WindowHubOfferFormBinder().bind(
        _plan(context),
        _scene(
            "Podstawowe parametry okna",
            (_element("combobox", "Wybierz kolor profili", "1054"),),
        ),
    )

    color = next(
        item for item in binding.fields
        if item.field_name is None
    )

    assert color.status == WindowHubBindingStatus.FIELD_MAPPING_MISSING
    assert color.element is None


def test_wrong_application_and_unknown_step_do_not_bind_controls():
    binder = WindowHubOfferFormBinder()
    plan = _plan()

    wrong_app = binder.bind(
        plan,
        _scene(
            "Dodawanie nowej pozycji",
            (_element("edit", "Ile sztuk", "1001"),),
            application="Code.exe",
        ),
    )
    unknown_step = binder.bind(
        plan,
        _scene(
            "Customer dialog",
            (_element("edit", "Ile sztuk", "1001"),),
        ),
    )

    assert wrong_app.step is None
    assert unknown_step.step is None
    assert wrong_app.reason == "windowhub_step_not_observed"
    assert unknown_step.reason == "windowhub_step_not_observed"


def test_plan_fields_for_other_wizard_steps_are_not_bound_in_current_step():
    binding = WindowHubOfferFormBinder().bind(
        _plan(),
        _scene(
            "Parametry okuć",
            (_element("combobox", "Wybierz profil", "1012"),),
        ),
    )

    quantity = next(
        item for item in binding.fields
        if item.field_name == "quantity_input"
    )
    hardware = next(
        item for item in binding.fields
        if item.field_name == "hardware_profile"
    )

    assert quantity.status == WindowHubBindingStatus.NOT_CURRENT_STEP
    assert hardware.status == WindowHubBindingStatus.FIELD_MAPPING_MISSING
