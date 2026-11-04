"""One guarded, verified WindowHub transition from item to dimensions.

The runner deliberately does NOT select catalog values, enter dimensions,
advance beyond the dimensions screen, or save an offer.
"""
from __future__ import annotations

from app.agent.agent_action import AgentAction
from app.agent.offers.windowhub_offer_form_action import (
    PreparedWindowHubFormAction,
    WindowHubFormActionStatus,
)
from app.agent.offers.windowhub_offer_form_map import (
    WindowHubFormStep,
    WindowHubOfferFormMap,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.verification.expected_outcome import ExpectedOutcome


_UIA_SOURCES = frozenset({"windows_ui_automation", "windowhub_ui_automation"})


class WindowHubPositionToDimensionsPlanner:
    """Prepare exactly one Next click, after checking the saved input state."""

    def __init__(self, form_map: WindowHubOfferFormMap | None = None):
        self.form_map = form_map or WindowHubOfferFormMap()

    def prepare(self, scene: ScreenScene, *, expected_quantity: int):
        if not isinstance(scene, ScreenScene):
            raise TypeError("windowhub_navigation_scene_invalid")
        if (
            isinstance(expected_quantity, bool)
            or not isinstance(expected_quantity, int)
            or expected_quantity < 1
        ):
            return self._blocked("The expected quantity must be a positive integer.")

        snapshot = self.form_map.inspect(scene)
        if snapshot is None:
            return self._blocked("The active WindowHub wizard step is not recognized.")
        if snapshot.step is WindowHubFormStep.DIMENSIONS:
            return PreparedWindowHubFormAction(
                field_name="wizard_next_dimensions",
                status=WindowHubFormActionStatus.ALREADY_SATISFIED,
                reason="The dimensions step is already active; no click is needed.",
            )
        if snapshot.step is not WindowHubFormStep.POSITION:
            return self._blocked(
                "Navigation is only permitted from the new-position step."
            )

        quantity = snapshot.field("quantity_input")
        window_type = snapshot.field("item_type_window")
        if not self._field_matches(scene, quantity, "edit", "Ile sztuk", "1001"):
            return self._blocked("The quantity control is missing, unsafe, or ambiguous.")
        if not self._field_matches(scene, window_type, "radiobutton", "Okno", "1329"):
            return self._blocked("The Window product selector is missing or ambiguous.")
        if (
            (quantity.element.metadata or {}).get("current_value") is None
            or str(quantity.element.metadata["current_value"]).strip()
            != str(expected_quantity)
        ):
            return self._blocked("The visible quantity does not match the requested value.")
        if (window_type.element.metadata or {}).get("uia_selected") is not True:
            return self._blocked("The Window product type is not confirmed selected.")

        matches = [
            element
            for element in scene.elements
            if (
                element.kind == "button"
                and element.label == "Dalej >"
                and (element.metadata or {}).get("source") in _UIA_SOURCES
                and (element.metadata or {}).get("automation_id") == "12324"
                and (element.metadata or {}).get("uia_control_type") == "button"
                and (element.metadata or {}).get("uia_enabled") is True
                and (element.metadata or {}).get("uia_visible") is True
            )
        ]
        if len(matches) != 1 or not self._has_unique_runtime_id(scene, matches[0]):
            return self._blocked("The exact Next button is missing or ambiguous.")

        target = SemanticTargetQuery(
            role="button",
            label="Dalej >",
            automation_id="12324",
            uia_runtime_id=matches[0].metadata["uia_runtime_id"],
            description="WindowHub move from item to dimensions",
        )
        action = AgentAction(
            name="click_screen_element",
            description="Open the WindowHub dimensions step; do not save or advance further.",
            target=target,
            requires_environment_observation=True,
        )
        expectation = ExpectedOutcome(
            description="The WindowHub dimensions step is active.",
            expected_active_application="Okna.exe",
            expected_window_title="Wielkość okna",
        )
        return PreparedWindowHubFormAction(
            field_name="wizard_next_dimensions",
            status=WindowHubFormActionStatus.READY,
            reason="Next is uniquely identified; product and quantity are confirmed.",
            action=action,
            expected_outcome=expectation,
            runtime_id=target.uia_runtime_id,
            required_quantity=str(expected_quantity),
        )

    @classmethod
    def _field_matches(cls, scene, match, role, label, automation_id):
        if match is None or match.status != "matched" or match.enabled is not True:
            return False
        element = match.element
        if element is None or element.kind != role or element.label != label:
            return False
        metadata = element.metadata or {}
        return (
            metadata.get("source") in _UIA_SOURCES
            and metadata.get("automation_id") == automation_id
            and metadata.get("uia_control_type") == role
            and metadata.get("uia_enabled") is True
            and metadata.get("uia_visible") is True
            and cls._has_unique_runtime_id(scene, element)
        )

    @staticmethod
    def _has_unique_runtime_id(scene, element):
        metadata = element.metadata or {}
        runtime_id = metadata.get("uia_runtime_id")
        return (
            isinstance(runtime_id, str)
            and bool(runtime_id.strip())
            and sum(
                1
                for candidate in scene.elements
                if (
                    (candidate.metadata or {}).get("source") in _UIA_SOURCES
                    and (candidate.metadata or {}).get("uia_runtime_id") == runtime_id
                )
            ) == 1
        )

    @staticmethod
    def _blocked(reason):
        return PreparedWindowHubFormAction(
            field_name="wizard_next_dimensions",
            status=WindowHubFormActionStatus.BLOCKED,
            reason=reason,
        )
