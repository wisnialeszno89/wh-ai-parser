"""Business-goal planner for creating a first WindowHub offer.

Every decision is based on the current semantic observation and desired business
state, not a scripted list of screen coordinates. This module does not click
or type: executor capabilities are authorized separately after verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.agent.offers.windowhub_offer_form_map import (
    WindowHubFormStep,
    WindowHubOfferFormMap,
    normalize_uia_text,
)
from app.agent.offers.windowhub_position_mission import WindowPositionRequest


class OfferDecision(str, Enum):
    OPEN_NEW_OFFER = "open_new_offer"
    SELECT_TEST_CUSTOMER = "select_test_customer"
    SET_PRICE_PREFERENCES = "set_price_preferences"
    CONFIRM_DOCUMENT = "confirm_document"
    OPEN_NEW_POSITION = "open_new_position"
    DELEGATE_POSITION = "delegate_position"
    SET_WIDTH = "set_width"
    SET_HEIGHT = "set_height"
    ADVANCE_TO_PARAMETERS = "advance_to_parameters"
    SELECT_PROFILE_COLOR = "select_profile_color"
    FINISH_TO_MODIFIER = "finish_to_modifier"
    COMPLETE = "complete"
    STOP_UNSUPPORTED = "stop_unsupported"
    STOP_WRONG_ENVIRONMENT = "stop_wrong_environment"


@dataclass(frozen=True)
class NewWindowOfferGoal:
    position: WindowPositionRequest
    customer_policy: str = "test_existing_customer"
    excluded_prices: tuple[str, ...] = (
        "construction", "installation", "removal", "finishing",
    )
    color_outside: str = "antracyt"
    color_inside: str = "biały"
    finish_at_modifier: bool = True

    def __post_init__(self):
        if not isinstance(self.position, WindowPositionRequest):
            raise TypeError("offer_position_required")
        if self.customer_policy != "test_existing_customer":
            raise ValueError("only_explicit_test_customer_policy_is_supported")
        if set(self.excluded_prices) != {
            "construction", "installation", "removal", "finishing",
        }:
            raise ValueError("offer_excluded_prices_invalid")


@dataclass(frozen=True)
class OfferInstruction:
    decision: OfferDecision
    reason: str
    observed_stage: str
    field_name: str | None = None
    desired_value: object = None
    executable: bool = False


class NewWindowOfferMissionPlanner:
    """Route the desired offer to the next business-relevant missing state."""

    def __init__(self, form_map: WindowHubOfferFormMap | None = None):
        self.form_map = form_map or WindowHubOfferFormMap()

    @staticmethod
    def _controls(scene, label, kind=None):
        expected = normalize_uia_text(label)
        return [
            element for element in scene.elements
            if (kind is None or element.kind == kind)
            and normalize_uia_text(element.label or "") == expected
            and (element.metadata or {}).get("uia_visible") is True
        ]

    def decide(self, goal: NewWindowOfferGoal, scene) -> OfferInstruction:
        if not isinstance(goal, NewWindowOfferGoal):
            raise TypeError("new_window_offer_goal_required")
        application = scene.observation.state.active_application
        process_name = (
            application.replace("\\", "/").rsplit("/", 1)[-1].casefold()
            if isinstance(application, str) else ""
        )
        if process_name != "okna.exe":
            return OfferInstruction(
                OfferDecision.STOP_WRONG_ENVIRONMENT,
                "Foreground application is not WindowHub; locate and activate it first.",
                "other_application",
            )

        title = scene.observation.state.active_window_title or ""
        snapshot = self.form_map.inspect(scene)
        if snapshot is not None:
            if snapshot.step is WindowHubFormStep.POSITION:
                return OfferInstruction(
                    OfferDecision.DELEGATE_POSITION,
                    "Position wizard is visible; reuse the already verified position mission.",
                    "position",
                )
            if snapshot.step is WindowHubFormStep.DIMENSIONS:
                for name, value in (
                    ("width_1", goal.position.width_mm),
                    ("height_1", goal.position.height_mm),
                ):
                    field = snapshot.field(name)
                    if field is None or not field.is_unique or field.enabled is not True:
                        return OfferInstruction(
                            OfferDecision.STOP_UNSUPPORTED,
                            f"{name} is not uniquely identified and enabled.",
                            "dimensions",
                            name,
                        )
                    observed = (field.element.metadata or {}).get("current_value")
                    if str(observed).strip() != str(value):
                        return OfferInstruction(
                            OfferDecision.SET_WIDTH if name == "width_1" else OfferDecision.SET_HEIGHT,
                            "The visible dimension differs from the requested size.",
                            "dimensions",
                            name,
                            value,
                        )
                return OfferInstruction(
                    OfferDecision.ADVANCE_TO_PARAMETERS,
                    "Both complete-window dimensions now match the request.",
                    "dimensions",
                )
            if snapshot.step is WindowHubFormStep.BASIC_PARAMETERS:
                return OfferInstruction(
                    OfferDecision.SELECT_PROFILE_COLOR,
                    "Find catalog option for one-sided anthracite with white interior; do not infer it from substring alone.",
                    "basic_parameters",
                    "profile_color",
                    (goal.color_inside, goal.color_outside),
                )
            return OfferInstruction(
                OfferDecision.STOP_UNSUPPORTED,
                "Unmapped wizard stage; do not invent a finish or save action.",
                snapshot.step.value,
            )

        if normalize_uia_text(title) == normalize_uia_text("Właściwości dokumentu"):
            customers = self._controls(scene, "Klient", "combobox")
            if len(customers) != 1:
                return OfferInstruction(
                    OfferDecision.SELECT_TEST_CUSTOMER,
                    "Find one customer selector in the document dialog before choosing a test customer.",
                    "document_properties",
                    "customer",
                )
            customer_value = (customers[0].metadata or {}).get("current_value")
            if not isinstance(customer_value, str) or not customer_value.strip():
                return OfferInstruction(
                    OfferDecision.SELECT_TEST_CUSTOMER,
                    "No customer is selected. Choose a test customer from the actual database.",
                    "document_properties",
                    "customer",
                )
            exclusions = (
                ("exclude_construction_price", "Bez ceny konstrukcji"),
                ("exclude_installation_price", "Bez ceny montażu"),
                ("exclude_removal_price", "Bez ceny demontażu"),
                ("exclude_finishing_price", "Bez ceny wykończenia"),
            )
            for key, label in exclusions:
                matches = self._controls(scene, label, "checkbox")
                if len(matches) != 1:
                    return OfferInstruction(
                        OfferDecision.STOP_UNSUPPORTED,
                        f"Cannot uniquely observe pricing preference: {label}.",
                        "document_properties",
                        key,
                    )
                checked = (matches[0].metadata or {}).get("uia_checked")
                if checked is not True:
                    return OfferInstruction(
                        OfferDecision.SET_PRICE_PREFERENCES,
                        f"Pricing exclusion {label} is not confirmed checked.",
                        "document_properties",
                        key,
                        True,
                    )
            buttons = self._controls(scene, "OK", "button")
            if len(buttons) != 1:
                return OfferInstruction(
                    OfferDecision.STOP_UNSUPPORTED,
                    "Client and pricing are observed, but confirmation button is ambiguous.",
                    "document_properties",
                )
            return OfferInstruction(
                OfferDecision.CONFIRM_DOCUMENT,
                "A client and all four excluded prices are confirmed; document can be confirmed.",
                "document_properties",
            )

        if title.casefold().startswith("okna -"):
            if self._controls(scene, "NOWA OFERTA"):
                return OfferInstruction(
                    OfferDecision.OPEN_NEW_OFFER,
                    "New-offer control is visible on the start screen.",
                    "start",
                )
            return OfferInstruction(
                OfferDecision.OPEN_NEW_POSITION,
                "WindowHub document is open; locate a verified add-position action.",
                "document",
            )

        return OfferInstruction(
            OfferDecision.STOP_UNSUPPORTED,
            "No reliable semantic model exists for this WindowHub screen yet.",
            "unrecognized",
        )
