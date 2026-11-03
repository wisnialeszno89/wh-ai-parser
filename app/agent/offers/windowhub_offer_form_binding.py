"""Bind a WindowHub offer preview to the currently observed form step.

This layer is observational only. A successful match means a planned field
was found on the current screen; it never authorizes or performs an action.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.agent.offers.windowhub_offer_form_map import (
    WindowHubFormStep,
    WindowHubOfferFormMap,
)
from app.agent.offers.windowhub_offer_form_plan import (
    WindowHubOfferFormPlan,
    WindowHubPlanHandling,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


class WindowHubBindingStatus(str, Enum):
    PLAN_BLOCKED = "plan_blocked"
    FIELD_MAPPING_MISSING = "field_mapping_missing"
    NOT_CURRENT_STEP = "not_current_step"
    CONTROL_MISSING = "control_missing"
    CONTROL_AMBIGUOUS = "control_ambiguous"
    CONTROL_DISABLED = "control_disabled"
    MAPPING_UNVERIFIED = "mapping_unverified"
    CATALOG_SELECTION_UNVERIFIED = "catalog_selection_unverified"
    MATCHED_FOR_REVIEW = "matched_for_review"


@dataclass(frozen=True)
class WindowHubBoundPlanField:
    """A preview entry correlated with one current UIA control, if possible."""

    field_name: str | None
    desired_value: object
    status: WindowHubBindingStatus
    element: ScreenElement | None = None
    candidate_count: int = 0
    note: str = ""

    @property
    def is_uniquely_observed(self) -> bool:
        return (
            self.element is not None
            and self.candidate_count == 1
            and self.status in {
                WindowHubBindingStatus.MATCHED_FOR_REVIEW,
                WindowHubBindingStatus.MAPPING_UNVERIFIED,
                WindowHubBindingStatus.CATALOG_SELECTION_UNVERIFIED,
            }
        )

    @property
    def action_authorized(self) -> bool:
        # Deliberately false: observation and planning are not execution consent.
        return False


@dataclass(frozen=True)
class WindowHubOfferFormBinding:
    """Current-step correlation result for a non-executable offer plan."""

    step: WindowHubFormStep | None
    fields: tuple[WindowHubBoundPlanField, ...]
    reason: str = ""

    @property
    def action_authorized(self) -> bool:
        return False

    @property
    def uniquely_observed_fields(self) -> tuple[WindowHubBoundPlanField, ...]:
        return tuple(
            item for item in self.fields
            if item.is_uniquely_observed
        )


class WindowHubOfferFormBinder:
    """Correlate logical plan fields to one freshly observed UIA scene."""

    def __init__(
        self,
        form_map: WindowHubOfferFormMap | None = None,
    ) -> None:
        self.form_map = form_map or WindowHubOfferFormMap()

    def bind(
        self,
        plan: WindowHubOfferFormPlan,
        scene: ScreenScene,
    ) -> WindowHubOfferFormBinding:
        if not isinstance(plan, WindowHubOfferFormPlan):
            raise TypeError("windowhub_offer_binding_plan_invalid")
        snapshot = self.form_map.inspect(scene)
        if snapshot is None:
            return WindowHubOfferFormBinding(
                step=None,
                fields=tuple(
                    WindowHubBoundPlanField(
                        field_name=entry.field_name,
                        desired_value=entry.desired_value,
                        status=WindowHubBindingStatus.FIELD_MAPPING_MISSING,
                        note="No supported WindowHub wizard step is currently observed.",
                    )
                    for entry in plan.entries
                ),
                reason="windowhub_step_not_observed",
            )

        if plan.blockers:
            return WindowHubOfferFormBinding(
                step=snapshot.step,
                fields=tuple(
                    WindowHubBoundPlanField(
                        field_name=entry.field_name,
                        desired_value=entry.desired_value,
                        status=WindowHubBindingStatus.PLAN_BLOCKED,
                        note="The offer plan contains blockers; no field binding is allowed.",
                    )
                    for entry in plan.entries
                ),
                reason="offer_plan_blocked",
            )

        bound_fields = tuple(
            self._bind_entry(plan, snapshot, entry)
            for entry in plan.entries
        )
        return WindowHubOfferFormBinding(
            step=snapshot.step,
            fields=bound_fields,
            reason="observed_only_no_actions_authorized",
        )

    def _bind_entry(self, plan, snapshot, entry):
        if entry.field_name is None:
            return WindowHubBoundPlanField(
                field_name=None,
                desired_value=entry.desired_value,
                status=WindowHubBindingStatus.FIELD_MAPPING_MISSING,
                note=entry.note or "No logical UIA field is assigned.",
            )

        spec = self.form_map.spec_for_field(entry.field_name)
        if spec is None:
            return WindowHubBoundPlanField(
                field_name=entry.field_name,
                desired_value=entry.desired_value,
                status=WindowHubBindingStatus.FIELD_MAPPING_MISSING,
                note="No UIA selector specification exists for this logical field.",
            )

        if spec.step != snapshot.step:
            return WindowHubBoundPlanField(
                field_name=entry.field_name,
                desired_value=entry.desired_value,
                status=WindowHubBindingStatus.NOT_CURRENT_STEP,
                note=f"Field belongs to wizard step '{spec.step.value}'.",
            )

        match = snapshot.field(entry.field_name)
        if match is None or match.status == "missing":
            return WindowHubBoundPlanField(
                field_name=entry.field_name,
                desired_value=entry.desired_value,
                status=WindowHubBindingStatus.CONTROL_MISSING,
                note="The expected control is not visible in the current observation.",
            )
        if match.status == "ambiguous":
            return WindowHubBoundPlanField(
                field_name=entry.field_name,
                desired_value=entry.desired_value,
                status=WindowHubBindingStatus.CONTROL_AMBIGUOUS,
                candidate_count=match.candidate_count,
                note="More than one control matches; no target was selected.",
            )
        if match.enabled is not True:
            return WindowHubBoundPlanField(
                field_name=entry.field_name,
                desired_value=entry.desired_value,
                status=WindowHubBindingStatus.CONTROL_DISABLED,
                element=match.element,
                candidate_count=match.candidate_count,
                note="The uniquely observed control is not confirmed enabled.",
            )

        if entry.handling == WindowHubPlanHandling.MAPPING_UNVERIFIED:
            status = WindowHubBindingStatus.MAPPING_UNVERIFIED
        elif entry.handling == WindowHubPlanHandling.CATALOG_SELECTION:
            status = WindowHubBindingStatus.CATALOG_SELECTION_UNVERIFIED
        elif entry.handling in {
            WindowHubPlanHandling.DIRECT_VALUE,
            WindowHubPlanHandling.RADIO_SELECTION,
        }:
            status = WindowHubBindingStatus.MATCHED_FOR_REVIEW
        else:
            status = WindowHubBindingStatus.MAPPING_UNVERIFIED

        return WindowHubBoundPlanField(
            field_name=entry.field_name,
            desired_value=entry.desired_value,
            status=status,
            element=match.element,
            candidate_count=match.candidate_count,
            note=entry.note,
        )
