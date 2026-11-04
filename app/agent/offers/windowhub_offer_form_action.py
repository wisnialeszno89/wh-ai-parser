"""Prepare and run one guarded action on the WindowHub new-position form.

The planner is deliberately narrow: it can select the window item type and
write the requested quantity. All other fields remain blocked until their
catalog/geometry mappings are verified. Execution is delegated to the existing
AgentControlLoop and RobotGUIExecutor, which perform fresh observation and
post-action verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.offers.windowhub_offer_form_map import (
    WindowHubOfferFormMap,
    WindowHubFormStep,
)
from app.agent.offers.windowhub_offer_form_plan import (
    WindowHubPlannedField,
    WindowHubPlanHandling,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.verification.expected_outcome import ExpectedOutcome


_UIA_SOURCES = frozenset({
    "windows_ui_automation",
    "windowhub_ui_automation",
})


class WindowHubFormActionStatus(str, Enum):
    READY = "ready"
    ALREADY_SATISFIED = "already_satisfied"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class PreparedWindowHubFormAction:
    """One locally validated action and its exact semantic postcondition."""

    field_name: str
    status: WindowHubFormActionStatus
    reason: str
    action: AgentAction | None = None
    expected_outcome: ExpectedOutcome | None = None
    runtime_id: str | None = None
    required_quantity: str | None = None


class WindowHubOfferFormActionPlanner:
    """Prepare only explicitly supported first-step WindowHub field actions."""

    def __init__(
        self,
        form_map: WindowHubOfferFormMap | None = None,
    ) -> None:
        self.form_map = form_map or WindowHubOfferFormMap()

    def prepare_entry(
        self,
        scene: ScreenScene,
        entry: WindowHubPlannedField,
    ) -> PreparedWindowHubFormAction:
        if not isinstance(scene, ScreenScene):
            raise TypeError("windowhub_form_action_scene_invalid")
        if not isinstance(entry, WindowHubPlannedField):
            raise TypeError("windowhub_form_action_entry_invalid")

        field_name = entry.field_name
        if not isinstance(field_name, str) or not field_name.strip():
            return self._result(
                field_name or "",
                WindowHubFormActionStatus.UNSUPPORTED,
                "The plan entry has no concrete WindowHub field mapping.",
            )
        field_name = field_name.strip()

        snapshot = self.form_map.inspect(scene)
        if snapshot is None:
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The active application or WindowHub wizard step is not recognized.",
            )
        dimension_field = field_name in {"width_1", "height_1"}
        required_step = (
            WindowHubFormStep.DIMENSIONS if dimension_field
            else WindowHubFormStep.POSITION
        )
        if snapshot.step is not required_step:
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The requested field is not on the currently verified wizard step.",
            )

        spec = self.form_map.spec_for_field(field_name)
        if spec is None:
            return self._result(
                field_name,
                WindowHubFormActionStatus.UNSUPPORTED,
                "No observed WindowHub field specification exists.",
            )
        if spec.step is not required_step:
            return self._result(
                field_name,
                WindowHubFormActionStatus.UNSUPPORTED,
                "The field does not belong to the required wizard step.",
            )

        match = snapshot.field(field_name)
        if match is None or match.status != "matched" or match.element is None:
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The current field is missing or ambiguous.",
            )
        if match.enabled is not True:
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The current field is not confirmed enabled.",
            )

        element = match.element
        metadata = element.metadata or {}
        source = metadata.get("source")
        runtime_id = metadata.get("uia_runtime_id")
        control_type = metadata.get("uia_control_type")

        if source not in _UIA_SOURCES:
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The target has no approved Windows UI Automation provenance.",
            )
        if metadata.get("uia_visible") is not True:
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The target is not confirmed visible.",
            )
        if metadata.get("uia_enabled") is not True:
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The target is not confirmed enabled.",
            )
        if (
            not isinstance(runtime_id, str)
            or not runtime_id.strip()
            or self._runtime_id_count(scene, runtime_id) != 1
        ):
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The target UIA RuntimeId is missing or not unique.",
            )
        if (
            control_type != spec.control_type
            or element.kind.casefold() != spec.control_type
            or metadata.get("automation_id") != spec.automation_id
        ):
            return self._result(
                field_name,
                WindowHubFormActionStatus.BLOCKED,
                "The observed control role or AutomationId does not match the field map.",
            )

        target = SemanticTargetQuery(
            role=spec.control_type,
            label=spec.label,
            automation_id=spec.automation_id,
            uia_runtime_id=runtime_id,
            description=f"WindowHub {spec.control_type} '{spec.label}'",
        )

        if (
            field_name == "item_type_window"
            and entry.handling is WindowHubPlanHandling.RADIO_SELECTION
        ):
            if entry.desired_value is not True:
                return self._result(
                    field_name,
                    WindowHubFormActionStatus.UNSUPPORTED,
                    "This first radio action only supports selecting the Window item type.",
                )
            selected = metadata.get("uia_selected")
            if not isinstance(selected, bool):
                return self._result(
                    field_name,
                    WindowHubFormActionStatus.BLOCKED,
                    "The radio selection state is unknown; focus is not a substitute.",
                )
            if selected is True:
                return self._result(
                    field_name,
                    WindowHubFormActionStatus.ALREADY_SATISFIED,
                    "The Window item type is already selected; no click is needed.",
                    runtime_id=runtime_id,
                )

            action = AgentAction(
                name="click_screen_element",
                description="Select the Window item type in the current WindowHub position.",
                target=target,
                requires_environment_observation=True,
            )
            expected = ExpectedOutcome(
                description="The Window item type is selected.",
                expected_element_label=spec.label,
                expected_element_state_name="uia_selected",
                expected_element_state_value=True,
                expected_element_uia_runtime_id=runtime_id,
                expected_element_automation_id=spec.automation_id,
            )
            return self._result(
                field_name,
                WindowHubFormActionStatus.READY,
                "One uniquely identified radio control is ready for a guarded click.",
                action=action,
                expected_outcome=expected,
                runtime_id=runtime_id,
            )

        if (
            field_name == "quantity_input"
            and entry.handling is WindowHubPlanHandling.DIRECT_VALUE
        ):
            quantity = entry.desired_value
            if (
                isinstance(quantity, bool)
                or not isinstance(quantity, int)
                or quantity < 1
            ):
                return self._result(
                    field_name,
                    WindowHubFormActionStatus.BLOCKED,
                    "Quantity must be a positive integer.",
                )
            expected_value = str(quantity)
            current_value = metadata.get("current_value")
            if (
                isinstance(current_value, str)
                and current_value.strip() == expected_value
            ):
                return self._result(
                    field_name,
                    WindowHubFormActionStatus.ALREADY_SATISFIED,
                    "The quantity field already contains the requested value.",
                    runtime_id=runtime_id,
                )

            action = AgentAction(
                name="write_text",
                description="Enter the requested quantity in the WindowHub quantity field.",
                target=target,
                value=expected_value,
                requires_environment_observation=True,
            )
            expected = ExpectedOutcome(
                description="The WindowHub quantity field contains the requested quantity.",
                expected_element_label=spec.label,
                expected_element_current_value=expected_value,
                expected_element_uia_runtime_id=runtime_id,
                expected_element_automation_id=spec.automation_id,
            )
            return self._result(
                field_name,
                WindowHubFormActionStatus.READY,
                "The quantity field is uniquely identified and ready for one guarded write.",
                action=action,
                expected_outcome=expected,
                runtime_id=runtime_id,
            )

        if dimension_field and entry.handling is WindowHubPlanHandling.DIRECT_VALUE:
            dimension = entry.desired_value
            if (
                isinstance(dimension, bool)
                or not isinstance(dimension, int)
                or not 100 <= dimension <= 5000
            ):
                return self._result(
                    field_name,
                    WindowHubFormActionStatus.BLOCKED,
                    "The overall dimension must be an integer between 100 and 5000 mm.",
                )
            expected_value = str(dimension)
            if (
                isinstance(metadata.get("current_value"), str)
                and metadata["current_value"].strip() == expected_value
            ):
                return self._result(
                    field_name,
                    WindowHubFormActionStatus.ALREADY_SATISFIED,
                    "The overall dimension already matches the request.",
                    runtime_id=runtime_id,
                )
            action = AgentAction(
                name="write_text",
                description=f"Enter overall window dimension in {field_name}.",
                target=target,
                value=expected_value,
                requires_environment_observation=True,
            )
            expected = ExpectedOutcome(
                description=f"{field_name} contains the requested overall dimension.",
                expected_element_label=spec.label,
                expected_element_current_value=expected_value,
                expected_element_uia_runtime_id=runtime_id,
                expected_element_automation_id=spec.automation_id,
            )
            return self._result(
                field_name,
                WindowHubFormActionStatus.READY,
                "Uniquely observed overall dimension is ready for verified write.",
                action=action,
                expected_outcome=expected,
                runtime_id=runtime_id,
            )

        return self._result(
            field_name,
            WindowHubFormActionStatus.UNSUPPORTED,
            "This field operation is not enabled for live execution yet.",
        )

    @staticmethod
    def _runtime_id_count(scene: ScreenScene, runtime_id: str) -> int:
        return sum(
            1
            for candidate in scene.elements
            if (
                (candidate.metadata or {}).get("source") in _UIA_SOURCES
                and (candidate.metadata or {}).get("uia_runtime_id") == runtime_id
            )
        )

    @staticmethod
    def _result(
        field_name: str,
        status: WindowHubFormActionStatus,
        reason: str,
        *,
        action: AgentAction | None = None,
        expected_outcome: ExpectedOutcome | None = None,
        runtime_id: str | None = None,
    ) -> PreparedWindowHubFormAction:
        return PreparedWindowHubFormAction(
            field_name=field_name,
            status=status,
            reason=reason,
            action=action,
            expected_outcome=expected_outcome,
            runtime_id=runtime_id,
        )


class WindowHubOfferFormActionExecutor:
    """Run exactly one prepared action through the existing verified control loop."""

    @staticmethod
    def execute_prepared(
        prepared: PreparedWindowHubFormAction,
        scene: ScreenScene,
        control_loop: Any,
        *,
        request_message: str,
        session_id: str | None = None,
    ):
        if not isinstance(prepared, PreparedWindowHubFormAction):
            raise TypeError("windowhub_form_action_prepared_invalid")
        if prepared.status is not WindowHubFormActionStatus.READY:
            raise ValueError("windowhub_form_action_not_ready")
        if prepared.action is None or prepared.expected_outcome is None:
            raise ValueError("windowhub_form_action_contract_incomplete")
        if not callable(getattr(control_loop, "run", None)):
            raise TypeError("windowhub_form_action_control_loop_invalid")
        if not isinstance(request_message, str) or not request_message.strip():
            raise ValueError("windowhub_form_action_request_required")

        context = ExecutionContext(
            request=AgentRequest(
                message=request_message.strip(),
                session_id=session_id,
            )
        )
        context.update_scene(scene)
        target = prepared.action.target
        if not isinstance(target, SemanticTargetQuery):
            raise ValueError("windowhub_form_action_target_invalid")
        scope = {
            "field_name": prepared.field_name,
            "application": "Okna.exe",
            "window_title": (
                "Zakładanie nowego klienta"
                if prepared.field_name in {"new_customer_name", "confirm_new_customer"}
                else "Właściwości dokumentu"
                if prepared.field_name.startswith("exclude_") or prepared.field_name in {"confirm_document", "open_customer_lookup", "defer_document_properties", "new_customer_add"}
                else "Okna - Start1"
                if prepared.field_name == "start_new_offer"
                else "Wielkość okna"
                if prepared.field_name in {"width_1", "height_1"}
                else "Dodawanie nowej pozycji"
            ),
            "label": target.label,
            "control_type": target.role,
            "automation_id": target.automation_id,
            "uia_runtime_id": target.uia_runtime_id,
        }
        if prepared.field_name == "wizard_next_dimensions":
            if not (
                isinstance(prepared.required_quantity, str)
                and prepared.required_quantity.isdecimal()
                and int(prepared.required_quantity) > 0
            ):
                raise ValueError("windowhub_navigation_required_quantity_invalid")
            scope["required_quantity"] = prepared.required_quantity
        context.set_value("_windowhub_form_action_scope", scope)
        context.set_value(
            "expected_outcomes",
            {prepared.action.name: prepared.expected_outcome},
        )
        plan = ActionPlan(
            intent=AgentIntent.COMPUTER_USE,
            steps=(
                ActionStep(
                    index=1,
                    action=prepared.action,
                ),
            ),
            confidence=1.0,
        )
        return control_loop.run(plan=plan, context=context)
