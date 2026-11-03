"""Compile normalized offer data into a non-executable WindowHub form plan.

This module is deliberately a planning boundary, not an executor. It translates
known business values to logical form intents and reports every UI mapping that
still needs an observed, verified mapping before interaction can be enabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.agent.offers.offer_context import OfferContext
from app.agent.offers.offer_context_validator import OfferContextValidator
from app.wh.runtime.construction_project import ConstructionProject


class WindowHubPlanHandling(str, Enum):
    """How a planned value could be represented in the observed wizard."""

    RADIO_SELECTION = "radio_selection"
    DIRECT_VALUE = "direct_value"
    CATALOG_SELECTION = "catalog_selection"
    MAPPING_UNVERIFIED = "mapping_unverified"


@dataclass(frozen=True)
class WindowHubPlannedField:
    """A desired business value and its current form-mapping confidence."""

    field_name: str | None
    desired_value: object
    source: str
    handling: WindowHubPlanHandling
    note: str = ""


@dataclass(frozen=True)
class WindowHubOfferFormPlan:
    """Preview of intended WindowHub values; never directly executable."""

    entries: tuple[WindowHubPlannedField, ...] = ()
    blockers: tuple[str, ...] = ()
    review_items: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.blockers

    @property
    def requires_review(self) -> bool:
        return bool(self.review_items)

    @property
    def execution_enabled(self) -> bool:
        # A future executor must be separately implemented and authorized.
        return False


class WindowHubOfferFormPlanBuilder:
    """Build a conservative, value-only preview from OfferContext + project."""

    def __init__(
        self,
        validator: OfferContextValidator | None = None,
    ) -> None:
        self.validator = validator or OfferContextValidator()

    def build(
        self,
        context: OfferContext,
        project: ConstructionProject | None,
    ) -> WindowHubOfferFormPlan:
        if not isinstance(context, OfferContext):
            raise TypeError("windowhub_offer_plan_context_invalid")

        validation = self.validator.validate(context)
        blockers: list[str] = []
        review_items: list[str] = []

        blockers.extend(
            f"missing_context:{field}"
            for field in validation.missing_fields
        )
        blockers.extend(
            f"context_conflict:{conflict}"
            for conflict in validation.conflicts
        )

        if context.product_type != "window":
            blockers.append("unsupported_product_type_for_window_wizard")

        if project is None:
            blockers.append("construction_project_missing")
            return self._result((), blockers, review_items)

        schema = project.schema
        if (
            schema.width != context.width
            or schema.height != context.height
        ):
            blockers.append("compiled_dimensions_do_not_match_offer_context")

        if not schema.segments:
            blockers.append("compiled_construction_has_no_segments")

        profile = project.offer.profile
        if not profile.manufacturer.strip() or not profile.system.strip():
            blockers.append("compiled_profile_identity_missing")

        glazing_type = project.offer.glass.type
        if glazing_type not in {"2glass", "3glass"}:
            blockers.append("compiled_glazing_type_unsupported")

        if blockers:
            return self._result((), blockers, review_items)

        entries = [
            WindowHubPlannedField(
                field_name="item_type_window",
                desired_value=True,
                source="OfferContext.product_type",
                handling=WindowHubPlanHandling.RADIO_SELECTION,
                note="Window item type is exposed as a labeled radio button.",
            ),
            WindowHubPlannedField(
                field_name="quantity_input",
                desired_value=context.quantity,
                source="OfferContext.quantity",
                handling=WindowHubPlanHandling.DIRECT_VALUE,
                note="The quantity field is a labeled edit control.",
            ),
            WindowHubPlannedField(
                field_name="width_1",
                desired_value=schema.width,
                source="ConstructionProject.schema.width",
                handling=WindowHubPlanHandling.MAPPING_UNVERIFIED,
                note=(
                    "The wizard exposes five width controls. The meaning of "
                    "the first slot as overall frame width is not yet verified."
                ),
            ),
            WindowHubPlannedField(
                field_name="height_1",
                desired_value=schema.height,
                source="ConstructionProject.schema.height",
                handling=WindowHubPlanHandling.MAPPING_UNVERIFIED,
                note=(
                    "The wizard exposes five height controls. The meaning of "
                    "the first slot as overall frame height is not yet verified."
                ),
            ),
            WindowHubPlannedField(
                field_name="profile_system_picker",
                desired_value={
                    "manufacturer": profile.manufacturer,
                    "system": profile.system,
                },
                source="ConstructionProject.offer.profile",
                handling=WindowHubPlanHandling.CATALOG_SELECTION,
                note=(
                    "The profile control opens a selector; catalog option "
                    "identity and selection flow have not yet been observed."
                ),
            ),
            WindowHubPlannedField(
                field_name="glazing_package",
                desired_value=glazing_type,
                source="ConstructionProject.offer.glass.type",
                handling=WindowHubPlanHandling.CATALOG_SELECTION,
                note=(
                    "The glazing combo box is known, but its live options and "
                    "exact option-to-value mapping have not yet been observed."
                ),
            ),
        ]

        review_items.extend(
            (
                "dimension_control_slots_require_semantic_verification",
                "profile_selector_options_and_selection_flow_unverified",
                "glazing_package_options_unverified",
                "opening_pattern_to_windowhub_geometry_mapping_unverified",
            )
        )

        if context.color_inside is not None or context.color_outside is not None:
            entries.append(
                WindowHubPlannedField(
                    field_name=None,
                    desired_value={
                        "inside": project.offer.color_inside,
                        "outside": project.offer.color_outside,
                    },
                    source=(
                        "OfferContext.color_inside/"
                        "OfferContext.color_outside"
                    ),
                    handling=WindowHubPlanHandling.MAPPING_UNVERIFIED,
                    note=(
                        "Only one profile-color combo box has been observed. "
                        "Do not collapse inside and outside colors into one "
                        "selection until the real WindowHub behavior is verified."
                    ),
                )
            )
            review_items.append(
                "inside_outside_profile_color_mapping_unverified"
            )

        if len(schema.segments) > 1:
            review_items.append(
                "multi_segment_construction_requires_geometry_mapping"
            )

        return self._result(entries, blockers, review_items)

    @staticmethod
    def _result(
        entries,
        blockers,
        review_items,
    ) -> WindowHubOfferFormPlan:
        return WindowHubOfferFormPlan(
            entries=tuple(entries),
            blockers=tuple(dict.fromkeys(blockers)),
            review_items=tuple(dict.fromkeys(review_items)),
        )
