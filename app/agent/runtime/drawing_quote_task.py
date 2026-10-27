"""Approval-gated task checkpoint for a human-reviewed multi-window drawing.

This adapter records reviewed, structured window rows in a local checkpoint. Creating
the checkpoint never observes the desktop, drives WindowHub, saves an offer, or sends it.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.agent.offers.drawing_offer_specification_builder import (
    DrawingOfferSpecificationResult,
    ReviewedDrawingPosition,
)
from app.agent.runtime.resumable_task import TaskCheckpoint, TaskStatus


@dataclass(frozen=True)
class DrawingOfferTaskStartResult:
    """Result of preparing a local multi-window task checkpoint."""

    specification_result: DrawingOfferSpecificationResult
    checkpoint: TaskCheckpoint
    task_block_reason: str | None = None

    @property
    def task_created(self) -> bool:
        return True

    @property
    def requires_manual_review(self) -> bool:
        return True

    def to_payload(self) -> dict[str, object]:
        return {
            "status": "waiting_for_approval",
            "task_created": True,
            "requires_manual_review": True,
            "task_block_reason": self.task_block_reason,
            "specification": self.specification_result.to_payload(),
            "checkpoint": self.checkpoint.to_payload(),
            "windowhub_actions_executed": 0,
            "offer_saved": False,
            "offer_submitted": False,
        }


def _validate_specification_result(
    result: DrawingOfferSpecificationResult,
) -> tuple[ReviewedDrawingPosition, ...]:
    if not isinstance(result, DrawingOfferSpecificationResult):
        raise TypeError(
            "result must be a DrawingOfferSpecificationResult produced after visual review."
        )
    if (
        not isinstance(result.source_alias, str)
        or not result.source_alias.strip()
        or "/" in result.source_alias
        or "\\" in result.source_alias
        or ".." in result.source_alias
        or ":" in result.source_alias
    ):
        raise ValueError("A safe, filename-like source alias is required.")
    if (
        not isinstance(result.page_number, int)
        or isinstance(result.page_number, bool)
        or result.page_number < 1
    ):
        raise ValueError("page_number must be a positive integer.")

    positions = tuple(result.positions)
    if not positions:
        raise ValueError("At least one reviewed position is required.")
    position_numbers = [position.position_number for position in positions]
    if len(position_numbers) != len(set(position_numbers)):
        raise ValueError("Reviewed drawing positions must be unique.")
    if position_numbers != sorted(position_numbers):
        raise ValueError("Reviewed drawing positions must be sorted by position number.")

    specification = result.specification
    windows = tuple(specification.windows)
    if len(windows) != len(positions):
        raise ValueError(
            "The specification window list no longer matches the reviewed position list."
        )

    for position, window in zip(positions, windows):
        if not isinstance(position, ReviewedDrawingPosition):
            raise TypeError("Every reviewed row must be a ReviewedDrawingPosition.")
        position.validate()
        if (
            window.width != position.width_mm
            or window.height != position.height_mm
            or window.quantity != position.quantity
        ):
            raise ValueError(
                f"Specification data for position {position.position_number} "
                "does not match its human-reviewed values."
            )
        if any(
            not isinstance(value, str)
            for value in (
                window.profile,
                window.color_inside,
                window.color_outside,
                window.glazing,
                window.hardware,
                window.security,
                window.opening,
                window.room,
            )
        ):
            raise ValueError(
                f"Optional technical fields for position {position.position_number} "
                "must remain strings; missing facts must not be inferred."
            )
    return positions


def create_drawing_offer_task_checkpoint(
    result: DrawingOfferSpecificationResult,
    *,
    task_id: str | None = None,
    max_actions: int = 8,
    max_reasoning_calls: int = 8,
) -> TaskCheckpoint:
    """Create a checkpoint in WAITING_FOR_APPROVAL from a reviewed multi-row draft.

    The whole position set, values and the resulting domain specification are
    cross-checked. The resulting task is still blocked until a separate explicit
    approval call. No scene observation or GUI action is performed here.
    """
    positions = _validate_specification_result(result)
    specification = result.specification

    windows = [
        {
            "position_number": position.position_number,
            "width_mm": position.width_mm,
            "height_mm": position.height_mm,
            "quantity": position.quantity,
            "human_confirmed": True,
        }
        for position in positions
    ]
    total_quantity = sum(position.quantity for position in positions)
    if total_quantity < 1:
        raise ValueError("The reviewed drawing must contain at least one unit.")

    facts: dict[str, object] = {
        "product_type": "window",
        "windows": windows,
        "position_count": len(positions),
        "total_quantity": total_quantity,
        "drawing_source_alias": result.source_alias,
        "drawing_page_number": result.page_number,
        "human_review_confirmed": True,
        "customer_name": specification.customer_name.strip(),
    }
    # These are explicit values from the review/specification, not defaults.
    if specification.language.strip():
        facts["language"] = specification.language.strip()
    if specification.notes.strip():
        facts["notes"] = specification.notes.strip()
    if specification.installation:
        facts["installation"] = True
    if specification.transport:
        facts["transport"] = True

    citations = []
    for position in positions:
        common = {
            "source_alias": result.source_alias,
            "page_number": result.page_number,
            "source_kind": "image_document",
            "human_confirmed": True,
        }
        for field_name, raw_value in (
            (f"windows[{position.position_number}].width_mm", str(position.width_mm)),
            (f"windows[{position.position_number}].height_mm", str(position.height_mm)),
            (f"windows[{position.position_number}].quantity", str(position.quantity)),
        ):
            citations.append(
                {
                    "field_name": field_name,
                    "raw_value": raw_value,
                    "evidence_text": "Human-reviewed value checked against the original drawing.",
                    "source": dict(common),
                }
            )

    return TaskCheckpoint(
        task_id=task_id or f"drawing-offer-{uuid4().hex}",
        goal=(
            "Prepare a new WindowHub offer as a draft with exactly one separate "
            "line for every human-reviewed window position in the windows fact list. "
            "Preserve each position's width_mm, height_mm and quantity exactly. "
            "Do not merge different positions. Do not guess profile, glazing, "
            "opening, color, hardware or pricing. Never submit, send, publish or "
            "approve the offer; stop at the draft-save and verification boundary."
        ),
        facts=facts,
        required_fields=("product_type", "windows", "position_count", "total_quantity"),
        unresolved_issues=(),
        citations=tuple(citations),
        expected_application="WindowHub",
        status=TaskStatus.WAITING_FOR_APPROVAL,
        max_actions=max_actions,
        max_reasoning_calls=max_reasoning_calls,
        draft_only=True,
        approval_required=True,
        execution_approved=False,
    )
