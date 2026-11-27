"""Connect the verified WindowHub form planners to the live quote mission."""
from __future__ import annotations

from app.agent.agent_action import AgentAction
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus, WindowHubOfferFormActionPlanner,
)
from app.agent.offers.windowhub_offer_form_plan import WindowHubPlannedField, WindowHubPlanHandling
from app.agent.offers.windowhub_wizard_navigation import (
    WindowHubPositionToDimensionsPlanner, verified_windowhub_next_target,
)
from app.agent.runtime.computer_use_v2_action_session import ResolvedComputerUseV2Action


def choose_geometry_action(scene, *, stage, position):
    """Prepare a verified native action, its next stage, or a concrete blocker."""
    direct = WindowHubPlanHandling.DIRECT_VALUE
    fields = (
        (("item_type_window", True, WindowHubPlanHandling.RADIO_SELECTION),
         ("quantity_input", position.quantity, direct))
        if stage == "position" else
        (("width_1", position.width_mm, direct), ("height_1", position.height_mm, direct))
    )
    planner = WindowHubOfferFormActionPlanner()
    for field_name, value, handling in fields:
        entry = WindowHubPlannedField(
            field_name=field_name, desired_value=value,
            source="approved_position", handling=handling,
        )
        prepared = planner.prepare_entry(scene, entry)
        if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
            continue
        if prepared.status is not WindowHubFormActionStatus.READY:
            return None, stage, "geometry_control_unverified:" + field_name
        action = prepared.action
        postcondition = (
            {"kind": "entity_value_equals", "target_ref": None, "expected_value": action.value}
            if handling is direct else
            {"kind": "entity_state_equals", "target_ref": None,
             "state": "uia_selected", "expected_value": True}
        )
        return ResolvedComputerUseV2Action(action, None, postcondition), stage, ""

    if stage == "position":
        prepared = WindowHubPositionToDimensionsPlanner().prepare(
            scene, expected_quantity=position.quantity,
        )
        action = prepared.action
        next_stage = "dimensions"
    else:
        target = verified_windowhub_next_target(scene)
        action = AgentAction(
            name="click_screen_element",
            description="Move to the basic window parameters after checking the dimensions.",
            target=target, requires_environment_observation=True,
        ) if target is not None else None
        next_stage = "basic_parameters"
    if action is None:
        return None, stage, "geometry_control_unverified:next_button"
    return ResolvedComputerUseV2Action(action, None, {"kind": "scene_changed"}), next_stage, ""
