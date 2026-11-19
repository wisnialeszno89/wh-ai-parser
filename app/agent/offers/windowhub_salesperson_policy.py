"""Salesperson-style offer policy. Pure planning: no desktop actions or silent saves.

A position may remain incomplete. Catalog compatibility and screen readback are
execution responsibilities; this module never interprets a planned value as
a verified WindowHub value.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PositionStatus(str, Enum):
    PENDING = "pending"
    COMPLETE = "complete"
    PARTIAL = "partial"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SalesPosition:
    width_mm: int
    height_mm: int
    quantity: int = 1
    color_inside: str | None = None
    color_outside: str | None = None
    glazing_panes: int | None = None
    opening: str | None = None
    other_requirements: tuple[str, ...] = ()

    def __post_init__(self):
        for name in ("width_mm", "height_mm", "quantity"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"invalid_{name}")
        if self.glazing_panes is not None and (
            isinstance(self.glazing_panes, bool)
            or not isinstance(self.glazing_panes, int)
            or self.glazing_panes < 2
        ):
            raise ValueError("invalid_glazing_panes")
        if not isinstance(self.other_requirements, tuple):
            raise ValueError("other_requirements_must_be_tuple")


@dataclass(frozen=True)
class PlannedPosition:
    source: SalesPosition
    color_inside: str
    color_outside: str
    glazing_panes: int
    opening: str | None
    assumptions: tuple[str, ...]
    needs_opening_selection: bool


def plan_position(item: SalesPosition) -> PlannedPosition:
    """Apply user-authorized defaults, explicitly recording every assumption."""
    assumptions = []
    inside = (item.color_inside or "").strip()
    outside = (item.color_outside or "").strip()
    if not inside and not outside:
        inside = outside = "biały"
        assumptions.append("color_both_white_default")
    elif not inside:
        inside = outside
        assumptions.append("color_inside_matches_outside_assumed")
    elif not outside:
        outside = inside
        assumptions.append("color_outside_matches_inside_assumed")
    panes = item.glazing_panes
    if panes is None:
        panes = 2
        assumptions.append("two_pane_glazing_default")
    opening = (item.opening or "").strip() or None
    if opening is None:
        # Selection is deferred to verified construction/catalog context.
        assumptions.append("opening_requires_agent_choice")
    return PlannedPosition(
        source=item,
        color_inside=inside,
        color_outside=outside,
        glazing_panes=panes,
        opening=opening,
        assumptions=tuple(assumptions),
        needs_opening_selection=opening is None,
    )


class EntryRoute(str, Enum):
    ACTIVATE_WINDOWHUB = "activate_windowhub"
    WAIT_FOR_LOGIN = "wait_for_login"
    CREATE_OFFER = "create_offer"
    VERIFY_DOCUMENT = "verify_document"
    CONTINUE_EDITOR = "continue_editor"
    CONTINUE_POSITION = "continue_position"
    INSPECT_UNKNOWN_STAGE = "inspect_unknown_stage"


def route_from_stage(stage: str | None, *, existing_offer_authorized: bool = False) -> EntryRoute:
    """Determine initial route from observed UI, never assuming prior actions.

    Existing documents must be explicitly authorized to reuse before editing;
    accidental reuse of another customer's offer is not allowed.
    """
    if stage is None:
        return EntryRoute.ACTIVATE_WINDOWHUB
    if stage == "login":
        return EntryRoute.WAIT_FOR_LOGIN
    if stage == "start":
        return EntryRoute.CREATE_OFFER
    if stage in {"document_properties", "new_customer"}:
        return EntryRoute.VERIFY_DOCUMENT
    if stage in {"offer_document", "modifier"}:
        return EntryRoute.CONTINUE_EDITOR if existing_offer_authorized else EntryRoute.VERIFY_DOCUMENT
    if stage in {"position", "dimensions", "basic_parameters", "glazing", "hardware"}:
        return EntryRoute.CONTINUE_POSITION if existing_offer_authorized else EntryRoute.VERIFY_DOCUMENT
    return EntryRoute.INSPECT_UNKNOWN_STAGE


@dataclass(frozen=True)
class PositionResult:
    index: int
    status: PositionStatus
    dimensions_verified: bool = False
    complete_verified: bool = False
    draft_placeholder_verified: bool = False
    missing: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    note: str = ""
    substitutions: tuple[tuple[str, str, str], ...] = ()

    def __post_init__(self):
        if self.index < 1:
            raise ValueError("invalid_position_index")
        if self.status == PositionStatus.COMPLETE and not self.complete_verified:
            raise ValueError("complete_requires_readback")
        if self.status == PositionStatus.PARTIAL and not (
            self.dimensions_verified and self.draft_placeholder_verified
        ):
            raise ValueError("partial_requires_verified_placeholder")
        if self.status == PositionStatus.BLOCKED and self.complete_verified:
            raise ValueError("blocked_cannot_be_complete")


@dataclass
class OfferProgress:
    customer_verified: bool = False
    draft_saved_verified: bool = False
    positions: list[PositionResult] = field(default_factory=list)

    def record(self, result: PositionResult) -> None:
        if any(item.index == result.index for item in self.positions):
            raise ValueError("duplicate_position_index")
        self.positions.append(result)

    def next_position_index(self, total: int) -> int | None:
        if total < 1:
            raise ValueError("invalid_position_count")
        completed = {item.index for item in self.positions}
        return next((index for index in range(1, total + 1) if index not in completed), None)

    def report(self) -> dict[str, object]:
        return {
            "customer_verified": self.customer_verified,
            "draft_saved_verified": self.draft_saved_verified,
            "positions": [
                {
                    "index": item.index,
                    "status": item.status.value,
                    "dimensions_verified": item.dimensions_verified,
                    "complete_verified": item.complete_verified,
                    "draft_placeholder_verified": item.draft_placeholder_verified,
                    "missing": list(item.missing),
                    "assumptions": list(item.assumptions),
                    "note": item.note,
                    "substitutions": [
                        {"field": field, "requested": requested, "chosen": chosen}
                        for field, requested, chosen in item.substitutions
                    ],
                }
                for item in sorted(self.positions, key=lambda x: x.index)
            ],
            "complete_count": sum(x.status == PositionStatus.COMPLETE for x in self.positions),
            "partial_count": sum(x.status == PositionStatus.PARTIAL for x in self.positions),
            "blocked_count": sum(x.status == PositionStatus.BLOCKED for x in self.positions),
        }


    def salesperson_review_report(self) -> dict[str, object]:
        """Readback-only result for a human to inspect before any save.

        Never claim the live document is unsaved; it could predate this run.
        """
        report = self.report()
        report.update({
            "workflow_state": "awaiting_salesperson_review",
            "agent_save_performed": False,
            "save_authorized": False,
            "requires_human_review": True,
            "required_checks": [
                "Compare every completed position with the original customer enquiry",
                "Approve or correct all reported technical substitutions",
                "Review all partial, missing and blocked fields",
                "Verify totals, discount, VAT and preview before authorizing save",
            ],
        })
        return report
