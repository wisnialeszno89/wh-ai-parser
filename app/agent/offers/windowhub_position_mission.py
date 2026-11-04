"""Unified, conservative WindowHub position mission (planning only).

A mission describes business intent and progress. It does not synthesize
unproven GUI operations, click buttons or save offers. The existing
verified single-field actions remain the only execution entry points.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.agent.offers.windowhub_offer_form_map import (
    WindowHubFormStep,
    WindowHubOfferFormMap,
)
from app.agent.perception.screen_scene import ScreenScene


class MissionDecision(str, Enum):
    WRITE_QUANTITY = "write_quantity"
    NAVIGATE_TO_DIMENSIONS = "navigate_to_dimensions"
    COLLECT_DIMENSIONS_CAPABILITY = "collect_dimensions_capability"
    COLLECT_BASIC_PARAMETERS_CAPABILITY = "collect_basic_parameters_capability"
    COLLECT_GLAZING_CAPABILITY = "collect_glazing_capability"
    COLLECT_HARDWARE_CAPABILITY = "collect_hardware_capability"
    STOP_UNSUPPORTED = "stop_unsupported"
    STOP_WRONG_ENVIRONMENT = "stop_wrong_environment"


@dataclass(frozen=True)
class WindowPositionRequest:
    quantity: int
    width_mm: int
    height_mm: int
    profile_system: str | None = None
    glazing: str | None = None

    def __post_init__(self):
        for name in ("quantity", "width_mm", "height_mm"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"window_position_{name}_invalid")


@dataclass(frozen=True)
class MissionInstruction:
    decision: MissionDecision
    reason: str
    step: WindowHubFormStep | None
    executable: bool = False


class WindowPositionMissionPlanner:
    """Plan from freshly observed wizard state, never from assumed progress."""

    def __init__(self, form_map: WindowHubOfferFormMap | None = None):
        self.form_map = form_map or WindowHubOfferFormMap()

    def decide(
        self, request: WindowPositionRequest, scene: ScreenScene
    ) -> MissionInstruction:
        if not isinstance(request, WindowPositionRequest):
            raise TypeError("window_position_request_required")
        snapshot = self.form_map.inspect(scene)
        if snapshot is None:
            return MissionInstruction(
                MissionDecision.STOP_WRONG_ENVIRONMENT,
                "WindowHub wizard is not the active recognized window.",
                None,
            )
        step = snapshot.step
        if step is WindowHubFormStep.POSITION:
            quantity = snapshot.field("quantity_input")
            window = snapshot.field("item_type_window")
            if not (
                window is not None and window.is_unique
                and window.enabled is True
                and (window.element.metadata or {}).get("uia_selected") is True
            ):
                return MissionInstruction(
                    MissionDecision.STOP_UNSUPPORTED,
                    "Window item type is not uniquely confirmed selected.",
                    step,
                )
            if not (
                quantity is not None and quantity.is_unique
                and quantity.enabled is True
            ):
                return MissionInstruction(
                    MissionDecision.STOP_UNSUPPORTED,
                    "Quantity field is not uniquely identified.",
                    step,
                )
            actual = (quantity.element.metadata or {}).get("current_value")
            if not isinstance(actual, str) or actual.strip() != str(request.quantity):
                return MissionInstruction(
                    MissionDecision.WRITE_QUANTITY,
                    "Quantity differs from the request; use the existing guarded writer.",
                    step,
                    executable=True,
                )
            return MissionInstruction(
                MissionDecision.NAVIGATE_TO_DIMENSIONS,
                "Quantity and window type confirmed; use guarded Next action.",
                step,
                executable=True,
            )

        followups = {
            WindowHubFormStep.DIMENSIONS: (
                MissionDecision.COLLECT_DIMENSIONS_CAPABILITY,
                "Dimensions are identified, but their construction semantics and verified write actions must be proven before execution.",
            ),
            WindowHubFormStep.BASIC_PARAMETERS: (
                MissionDecision.COLLECT_BASIC_PARAMETERS_CAPABILITY,
                "Basic profile options require catalog-aware mapping and verified controls.",
            ),
            WindowHubFormStep.GLAZING: (
                MissionDecision.COLLECT_GLAZING_CAPABILITY,
                "Glazing options require verified compatibility and catalog values.",
            ),
            WindowHubFormStep.HARDWARE: (
                MissionDecision.COLLECT_HARDWARE_CAPABILITY,
                "Hardware options require verified construction-specific mapping.",
            ),
        }
        if step in followups:
            decision, reason = followups[step]
            return MissionInstruction(decision, reason, step)
        return MissionInstruction(
            MissionDecision.STOP_UNSUPPORTED,
            "This wizard step is not supported by the first window-position mission.",
            step,
        )
