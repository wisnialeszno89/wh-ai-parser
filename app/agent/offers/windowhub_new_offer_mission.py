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
    OPEN_NEW_CUSTOMER = "open_new_customer"
    SET_NEW_CUSTOMER_NAME = "set_new_customer_name"
    CONFIRM_NEW_CUSTOMER = "confirm_new_customer"
    DEFER_CUSTOMER_PREFERENCES = "defer_customer_preferences"
    OPEN_CUSTOMER_LOOKUP = "open_customer_lookup"
    INSPECT_CUSTOMER_LOOKUP = "inspect_customer_lookup"
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
    customer_name: str | None = None
    excluded_prices: tuple[str, ...] = (
        "construction", "installation", "removal", "finishing",
    )
    color_outside: str = "antracyt"
    color_inside: str = "biały"
    finish_at_modifier: bool = True

    def __post_init__(self):
        if not isinstance(self.position, WindowPositionRequest):
            raise TypeError("offer_position_required")
        if self.customer_policy not in {"test_existing_customer", "defer_to_salesperson", "select_blank_customer", "create_customer"}:
            raise ValueError("unsupported_customer_policy")
        if self.customer_policy == "create_customer":
            if (
                not isinstance(self.customer_name, str)
                or not self.customer_name.strip()
                or len(self.customer_name.strip()) > 100
                or any(ord(ch) < 32 for ch in self.customer_name)
            ):
                raise ValueError("valid_new_customer_name_required")
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

        if normalize_uia_text(title) == normalize_uia_text("Zakładanie nowego klienta"):
            name_fields = self._controls(scene, "Firma", "edit")
            if len(name_fields) != 1:
                return OfferInstruction(
                    OfferDecision.STOP_UNSUPPORTED,
                    "New customer Firma field is not uniquely recognized.",
                    "new_customer", "new_customer_name",
                )
            observed = (name_fields[0].metadata or {}).get("current_value")
            if not isinstance(observed, str) or observed.strip() != (goal.customer_name or ""):
                return OfferInstruction(
                    OfferDecision.SET_NEW_CUSTOMER_NAME,
                    "New customer name differs from the requested value.",
                    "new_customer", "new_customer_name", goal.customer_name,
                )
            return OfferInstruction(
                OfferDecision.CONFIRM_NEW_CUSTOMER,
                "Requested customer name is observed; verify form before confirmation.",
                "new_customer",
            )

        if normalize_uia_text(title) == normalize_uia_text("Właściwości dokumentu"):
            if goal.customer_policy == "create_customer":
                return OfferInstruction(
                    OfferDecision.OPEN_NEW_CUSTOMER,
                    "Open native Add (+) to create requested customer.",
                    "document_properties", "new_customer_add", goal.customer_name,
                )
            # Blank customer is an explicit sales intent; it is never inferred
            # from the first visible row or an empty text cell.
            if goal.customer_policy == "defer_to_salesperson":
                return OfferInstruction(
                    OfferDecision.DEFER_CUSTOMER_PREFERENCES,
                    "User explicitly requested to postpone client and document preferences; verify transition after Cancel.",
                    "document_properties",
                    "defer_document_properties",
                )
            # Native DevExpress lookup is a button (IDC_ZAMAWIAJACY), not a
            # combobox. First detect its opened grid to prevent double-click.
            lookup_grids = [
                e for e in scene.elements
                if e.kind == "table"
                and (e.metadata or {}).get("automation_id") == "PART_GridControl"
                and (e.metadata or {}).get("uia_visible") is True
                and any(
                    isinstance(ancestor, dict)
                    and ancestor.get("automation_id") == "IDC_ZAMAWIAJACY"
                    for ancestor in (e.metadata or {}).get("uia_ancestor_structure", ())
                )
            ]
            if lookup_grids:
                return OfferInstruction(
                    OfferDecision.INSPECT_CUSTOMER_LOOKUP,
                    "Customer lookup grid is visible; inspect records and selection semantics.",
                    "customer_lookup",
                    "customer",
                )
            customers = self._controls(scene, "Klient", "combobox")
            # DevExpress LookUpEdit may expose the selected company via the
            # native customer control rather than a separate combobox.
            native_customers = [
                e for e in scene.elements
                if e.kind == "button"
                and (e.metadata or {}).get("automation_id") == "IDC_ZAMAWIAJACY"
                and (e.metadata or {}).get("uia_visible") is True
            ]
            if goal.customer_name is not None and len(native_customers) == 1:
                selected = (native_customers[0].metadata or {}).get("current_value")
                if isinstance(selected, str) and selected.strip() == goal.customer_name.strip():
                    customers = [native_customers[0]]
            if goal.customer_name is not None and len(customers) != 1:
                return OfferInstruction(
                    OfferDecision.SELECT_TEST_CUSTOMER,
                    "New customer was created, but native lookup does not prove it is selected. Stop before another lookup.",
                    "document_properties", "customer",
                )
            if len(customers) != 1:
                lookup_buttons = [
                    e for e in scene.elements
                    if e.kind == "button"
                    and e.label == "LookUpEdit"
                    and (e.metadata or {}).get("automation_id") == "IDC_ZAMAWIAJACY"
                    and (e.metadata or {}).get("uia_visible") is True
                ]
                if len(lookup_buttons) == 1:
                    return OfferInstruction(
                        OfferDecision.OPEN_CUSTOMER_LOOKUP,
                        "Open the native customer LookupEdit; do not choose a row yet.",
                        "document_properties",
                        "customer",
                    )
                return OfferInstruction(
                    OfferDecision.SELECT_TEST_CUSTOMER,
                    "No unique customer lookup is observable.",
                    "document_properties",
                    "customer",
                )
            customer_value = (customers[0].metadata or {}).get("current_value")
            if (
                goal.customer_name is not None
                and (not isinstance(customer_value, str) or customer_value.strip() != goal.customer_name.strip())
            ):
                return OfferInstruction(
                    OfferDecision.SELECT_TEST_CUSTOMER,
                    "New customer is not yet proven selected in document; do not confirm another customer.",
                    "document_properties", "customer",
                )
            if not isinstance(customer_value, str) or not customer_value.strip():
                return OfferInstruction(
                    OfferDecision.SELECT_TEST_CUSTOMER,
                    "No customer is selected. Choose a test customer from the actual database.",
                    "document_properties",
                    "customer",
                )
            exclusions = (
                ("exclude_construction_price", "Bez ceny konstrukcji", "IDC_CENA_OKNA"),
                ("exclude_installation_price", "Bez ceny montażu", "IDC_CENA_MONTAZU"),
                ("exclude_removal_price", "Bez ceny demontażu", "IDC_CENA_DEMONTAZU"),
                ("exclude_finishing_price", "Bez ceny wykończenia", "IDC_CENA_WYKONCZENIA"),
            )
            for key, label, automation_id in exclusions:
                matches = [
                    e for e in scene.elements
                    if e.kind == "checkbox"
                    and (e.metadata or {}).get("automation_id") == automation_id
                    and (e.metadata or {}).get("uia_visible") is True
                    and (e.metadata or {}).get("uia_enabled") is True
                ]
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

        if normalize_uia_text(title).startswith(normalize_uia_text("Okna - Start1")):
            new_offer = self._controls(scene, "NOWA OFERTA")
            if len(new_offer) == 1:
                return OfferInstruction(
                    OfferDecision.OPEN_NEW_OFFER,
                    "A single New Offer control is observed on the WindowHub start screen.",
                    "start",
                )
            return OfferInstruction(
                OfferDecision.STOP_UNSUPPORTED,
                "The start screen is visible, but New Offer is not a unique observed semantic target.",
                "start",
            )

        if title.casefold().startswith("okna -"):
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
