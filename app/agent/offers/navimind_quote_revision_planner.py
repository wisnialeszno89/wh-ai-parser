"""Evidence-based choice: revise existing quotation or create a new draft.

The decision uses a conservative estimated edit cost, not a hard-coded
percentage of changed fields. Nothing is edited, deleted or saved here.
A newer quote must preserve provenance and requires user approval for any
irreversible operation; a rebuild is a *new UNSAVED draft*, not destruction.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RevisionRoute(str, Enum):
    EDIT_EXISTING = "edit_existing"
    REBUILD_DRAFT = "rebuild_draft"
    REVIEW = "review"


@dataclass(frozen=True)
class QuoteChange:
    position_id: str
    field: str
    before: str | None
    after: str | None
    # Evidence-backed estimated steps, including verification.
    edit_steps: int
    rebuild_steps: int
    can_edit_existing: bool
    independently_observed: bool
    dependencies: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.position_id.strip() or not self.field.strip():
            raise ValueError("change_identity_required")
        if type(self.edit_steps) is not int or self.edit_steps < 0:
            raise ValueError("invalid_edit_steps")
        if type(self.rebuild_steps) is not int or self.rebuild_steps < 0:
            raise ValueError("invalid_rebuild_steps")
        if self.before == self.after:
            raise ValueError("no_effective_change")


@dataclass(frozen=True)
class QuoteRevisionPlan:
    route: RevisionRoute
    reason: str
    target_document: str
    changes: tuple[QuoteChange, ...]
    edit_cost: int | None
    rebuild_cost: int | None
    requires_fresh_readback: bool = True
    requires_salesperson_review: bool = True
    create_unsaved_draft_only: bool = True
    original_document_preserved: bool = True
    save_authorized: bool = False
    send_authorized: bool = False
    production_approved: bool = False


def plan_quote_revision(
    *,
    document_key: str, changes: tuple[QuoteChange, ...],
    exact_document_verified: bool,
    readback_fresh: bool,
    rebuild_possible: bool,
    rebuild_base_steps: int,
    preserve_existing_preferred: bool = True,
) -> QuoteRevisionPlan:
    if not isinstance(document_key, str) or not document_key.strip() or not changes:
        raise ValueError("pinned_document_and_changes_required")
    if len({(c.position_id, c.field) for c in changes}) != len(changes):
        raise ValueError("duplicate_field_changes")
    if type(rebuild_base_steps) is not int or rebuild_base_steps < 0:
        raise ValueError("invalid_rebuild_cost")
    def result(route, reason, edit=None, rebuild=None):
        return QuoteRevisionPlan(route, reason, document_key, changes, edit, rebuild)
    if not exact_document_verified or not readback_fresh:
        return result(RevisionRoute.REVIEW, "fresh_exact_offer_required")
    if not all(change.independently_observed for change in changes):
        return result(RevisionRoute.REVIEW, "unverified_existing_values")
    if any(
        dependency not in {"description", "quantity", "dimensions", "price", "colour", "glazing", "image", "hardware"}
        for change in changes for dependency in change.dependencies
    ):
        return result(RevisionRoute.REVIEW, "unknown_change_dependencies")
    edits_supported = all(change.can_edit_existing for change in changes)
    edit_cost = (sum(c.edit_steps for c in changes)
                 if edits_supported else None)
    rebuild_cost = (rebuild_base_steps + sum(c.rebuild_steps for c in changes)
                    if rebuild_possible else None)
    if edit_cost is None and rebuild_cost is None:
        return result(RevisionRoute.REVIEW, "no_verified_edit_or_rebuild_path")
    if edit_cost is None:
        return result(RevisionRoute.REBUILD_DRAFT, "existing_edit_not_supported",
                      edit_cost, rebuild_cost)
    if rebuild_cost is None:
        return result(RevisionRoute.EDIT_EXISTING, "rebuild_not_supported",
                      edit_cost, rebuild_cost)
    if edit_cost < rebuild_cost or (edit_cost == rebuild_cost and preserve_existing_preferred):
        return result(RevisionRoute.EDIT_EXISTING, "lower_or_equal_verified_edit_effort",
                      edit_cost, rebuild_cost)
    return result(RevisionRoute.REBUILD_DRAFT, "verified_rebuild_effort_lower",
                  edit_cost, rebuild_cost)
