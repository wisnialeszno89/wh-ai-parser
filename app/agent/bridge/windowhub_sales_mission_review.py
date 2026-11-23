"""Evidence-based salesperson review report for an UNSAVED WindowHub mission.

This module never operates WindowHub. It reconciles validated enquiry requirements
with explicitly recorded application observations. Missing evidence is NOT success.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewEvidence:
    """Single independently verified application observation, not a model guess."""
    position: int
    field: str
    observed: Any
    verified: bool
    source: str


_ALLOWED_POSITION_FIELDS = frozenset({
    "width_mm", "height_mm", "quantity", "layout", "opening",
    "system", "color_external", "color_internal", "glazing_panes",
    "discount_percent", "roller_box_height_mm", "roller_total_height_mm",
})


def build_review_report(mission: dict, evidence: tuple[ReviewEvidence, ...] = (),
                        *, customer_selection: str = "not_observed",
                        customer_commit_verified: bool = False) -> dict:
    """Produce auditable summary without inferring successful actions.

    Evidence must be issued by the local, verified WindowHub readback layer.
    A raw model decision, screenshot click or user query is not valid evidence.
    Values conflicting with the request are deviations, never hidden.
    """
    if not isinstance(mission, dict) or not isinstance(mission.get("positions"), list):
        raise ValueError("invalid_mission")
    expected_positions = {row["index"]: row for row in mission["positions"]}
    if len(expected_positions) != len(mission["positions"]):
        raise ValueError("duplicate_position_index")
    observed: dict[tuple[int, str], ReviewEvidence] = {}
    for item in evidence:
        if not isinstance(item, ReviewEvidence) or item.position not in expected_positions:
            raise ValueError("invalid_evidence_position")
        if item.field not in _ALLOWED_POSITION_FIELDS:
            raise ValueError("invalid_evidence_field")
        if not item.verified or item.source != "windowhub_live_readback":
            raise ValueError("unverified_evidence")
        key = (item.position, item.field)
        if key in observed:
            raise ValueError("conflicting_or_repeated_evidence")
        observed[key] = item

    globals_ = mission.get("global") or {}
    reviews = []
    outstanding = []
    verified_fields = 0
    for idx, requested in expected_positions.items():
        expected = {
            "width_mm": requested.get("width_mm"),
            "height_mm": requested.get("height_mm"),
            "quantity": requested.get("quantity"),
            "layout": requested.get("layout"),
            "opening": requested.get("opening"),
            "system": globals_.get("system"),
            "color_external": globals_.get("color_external"),
            "color_internal": globals_.get("color_internal"),
            "glazing_panes": globals_.get("glazing_panes"),
            "discount_percent": globals_.get("discount_window_percent"),
        }
        if requested.get("box_above_marked"):
            box = requested.get("roller_position") or {}
            expected["roller_box_height_mm"] = box.get("box_height_mm")
            expected["roller_total_height_mm"] = box.get("overall_height_mm")

        fields = []
        for field, requirement in expected.items():
            proof = observed.get((idx, field))
            if proof is None:
                status = "requires_live_readback"
                actual = None
            elif requirement is None:
                # Unknown size from enquiry is resolved by live catalogue selection,
                # but still needs salesperson approval for inferred dimensions.
                status = "catalogue_value_needs_salesperson_review"
                actual = proof.observed
                verified_fields += 1
            elif proof.observed == requirement:
                status = "verified_matches_request"
                actual = proof.observed
                verified_fields += 1
            else:
                status = "verified_differs_from_request"
                actual = proof.observed
                verified_fields += 1

            if status != "verified_matches_request":
                outstanding.append({"position": idx, "field": field, "status": status})
            fields.append({
                "field": field,
                "requested": requirement,
                "observed": actual,
                "status": status,
            })
        reviews.append({
            "position": idx,
            "kind": requested.get("kind", "window"),
            "fields": fields,
            "fully_matches_request": all(f["status"] == "verified_matches_request" for f in fields),
        })

    customer_needs_review = not customer_commit_verified
    if customer_needs_review:
        outstanding.insert(0, {
            "position": None,
            "field": "customer",
            "status": "customer_commit_not_verified",
        })
    return {
        "schema": "navimind.windowhub.salesperson_review.v1",
        "mission_id": mission.get("mission_id"),
        "requested_customer": (mission.get("customer") or {}).get("exact_name"),
        "customer_selection": customer_selection,
        "customer_commit_verified": bool(customer_commit_verified),
        "positions": reviews,
        "verified_field_count": verified_fields,
        "unresolved": outstanding,
        "report_available": True,
        "mission_complete_verified": False,
        "save_authorized": False,
        "send_authorized": False,
        "disclaimer": "Only independent WindowHub live readback counts as verified. No application work is implied by this report.",
    }


def compact_review_summary(report: dict) -> str:
    """Human-readable terminal summary with explicit scope limitations."""
    positions = report["positions"]
    exact = sum(item["fully_matches_request"] for item in positions)
    return (
        "Mission: " + str(report["mission_id"]) + "\n"
        + "Customer: " + str(report["requested_customer"]) + "\n"
        + "Customer selection: " + str(report["customer_selection"]) + "\n"
        + "Customer commit verified: " + str(report["customer_commit_verified"]) + "\n"
        + "Positions with all required fields verified: "
        + str(exact) + "/" + str(len(positions)) + "\n"
        + "Fields requiring review: " + str(len(report["unresolved"])) + "\n"
        + "Save/send authorized: NO | requires salesperson review: YES"
    )
