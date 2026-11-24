"""Offline NaviMind mission coordinator: goal -> route -> verified skill intents.

This is a pure planner, not a Windows executor. It never assumes clicking,
typing, pasting, or price changes succeeded. A Windows adapter must translate
proposed intents through V2 policy and independently read back every result.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuotePlan, QuoteRequest, QuoteRoute,
    TechnicalFinding, plan_commercial_quote,
)
from app.agent.runtime.portable_editor_skills import (
    Attachment, EditorOperation, EditorRequest, EditorTarget,
    EditorStep, plan_editor_step,
)


class MissionAction(str, Enum):
    OBSERVE = "observe"
    CREATE_POSITION = "create_position"
    WRITE_DESCRIPTION = "write_description"
    INSERT_IMAGE = "insert_image"
    SET_MANUAL_PRICE = "set_manual_price"
    REVIEW = "review"
    COMPLETE = "complete"


@dataclass(frozen=True)
class PositionTask:
    position_id: str
    request: QuoteRequest
    technical: TechnicalFinding
    # Explicit mission-level permission to leave an unpriced item in a
    # clearly marked unfinished draft and continue to the next position.
    # This NEVER authorizes a zero price, save, send or final quotation.
    allow_unpriced_draft: bool = False

    def __post_init__(self):
        if not self.position_id.strip():
            raise ValueError("position_id_required")


@dataclass(frozen=True)
class PositionReadback:
    """Only independently verified facts from the current live document."""
    position_id: str
    created_verified: bool = False
    description_verified: bool = False
    image_verified: bool = False
    price_verified: bool = False
    # The last observation must have checked the exact intended position.
    document_id: str = ""
    fresh: bool = False
    exact_position: bool = False


@dataclass(frozen=True)
class MissionScene:
    application: str
    document_id: str
    document_identity_verified: bool
    fresh: bool
    active_position_id: str | None
    quote_capabilities: QuoteCapabilities
    editor_target: EditorTarget | None = None


@dataclass(frozen=True)
class MissionIntent:
    action: MissionAction
    position_id: str | None
    reason: str
    proposed_route: QuoteRoute | None = None
    description: str | None = None
    image_reference: str | None = None
    price: str | None = None
    warnings: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    verified_completed: bool = False
    # No command sent by this module is executable on its own.
    requires_v2_executor: bool = False


def _trusted_readback(task: PositionTask, scene: MissionScene,
                      readbacks: tuple[PositionReadback, ...]) -> PositionReadback:
    matches = [r for r in readbacks if r.position_id == task.position_id]
    if len(matches) != 1:
        return PositionReadback(position_id=task.position_id)
    item = matches[0]
    if not (item.fresh and item.exact_position and item.document_id == scene.document_id):
        return PositionReadback(position_id=task.position_id)
    return item


def next_mission_intent(
    tasks: tuple[PositionTask, ...], scene: MissionScene,
    readbacks: tuple[PositionReadback, ...] = (),
    *,
    attempted_without_progress: tuple[str, ...] = (),
) -> MissionIntent:
    """Choose the next unverified requirement, never a new position by guess.

    A model can later rank proposed actions, but cannot override missing
    readback, a stale document, edit permission or a non-catalogue warning.
    """
    ids = [t.position_id for t in tasks]
    if not tasks or len(ids) != len(set(ids)):
        raise ValueError("nonempty_unique_positions_required")
    if (not scene.fresh or not scene.document_identity_verified
            or scene.application != "WindowHub" or not scene.document_id):
        return MissionIntent(MissionAction.OBSERVE, None, "fresh_exact_document_required")

    for task in tasks:
        plan = plan_commercial_quote(task.request, scene.quote_capabilities, task.technical)
        actual = _trusted_readback(task, scene, readbacks)
        if plan.route == QuoteRoute.MANUAL_REVIEW:
            return MissionIntent(MissionAction.REVIEW, task.position_id,
                                 "quotation_route_requires_salesperson",
                                 proposed_route=plan.route, warnings=plan.warnings,
                                 missing=plan.pending)
        if (plan.manual_unit_price is None
                and task.request.manual_unit_price is not None
                and not task.allow_unpriced_draft):
            return MissionIntent(MissionAction.REVIEW, task.position_id,
                                 "requested_manual_price_field_unavailable",
                                 proposed_route=plan.route, warnings=plan.warnings,
                                 missing=plan.pending)

        if not actual.created_verified:
            action = MissionAction.CREATE_POSITION
            reason = "position_not_independently_verified"
            data = dict(proposed_route=plan.route, description=plan.proposed_description,
                        warnings=plan.warnings, missing=plan.pending)
        elif not actual.description_verified:
            action = MissionAction.WRITE_DESCRIPTION
            reason = "description_not_independently_verified"
            data = dict(description=plan.proposed_description, warnings=plan.warnings,
                        missing=plan.pending)
            editor = scene.editor_target
            req = EditorRequest(
                EditorOperation.REPLACE_TEXT, text=plan.proposed_description,
                expected_document_id=scene.document_id,
                expected_position_id=task.position_id,
            )
            check = plan_editor_step(req, editor)
            if check.step != EditorStep.WRITE:
                return MissionIntent(
                    MissionAction.OBSERVE if check.step == EditorStep.INSPECT else MissionAction.REVIEW,
                    task.position_id, "description_editor:" + check.reason,
                    proposed_route=plan.route, warnings=plan.warnings, missing=plan.pending,
                )
        elif task.request.image_reference and not actual.image_verified:
            if not plan.image_ready:
                return MissionIntent(MissionAction.REVIEW, task.position_id,
                                     "image_requirements_unresolved",
                                     proposed_route=plan.route, warnings=plan.warnings,
                                     missing=plan.pending)
            req = EditorRequest(
                EditorOperation.INSERT_IMAGE,
                image=Attachment(plan.image_reference, True, True, True),
                expected_document_id=scene.document_id,
                expected_position_id=task.position_id,
            )
            check = plan_editor_step(req, scene.editor_target)
            if check.step != EditorStep.WRITE:
                return MissionIntent(
                    MissionAction.OBSERVE if check.step == EditorStep.INSPECT else MissionAction.REVIEW,
                    task.position_id, "image_editor:" + check.reason,
                    proposed_route=plan.route, warnings=plan.warnings, missing=plan.pending,
                )
            action = MissionAction.INSERT_IMAGE
            reason = "image_rendering_not_independently_verified"
            data = dict(image_reference=plan.image_reference, warnings=plan.warnings,
                        missing=plan.pending)
        elif plan.manual_unit_price is None and not actual.price_verified:
            if task.allow_unpriced_draft:
                # No verified source or no verified input field. Leave this
                # position unpriced and continue, without retrying blindly.
                # Final summary still reports it as INCOMPLETE.
                continue
            reason = (
                "requested_manual_price_field_unavailable"
                if task.request.manual_unit_price is not None
                else "catalogue_or_external_price_requires_independent_readback"
            )
            return MissionIntent(MissionAction.REVIEW, task.position_id,
                                 reason, proposed_route=plan.route,
                                 warnings=plan.warnings, missing=plan.pending)
        elif plan.manual_unit_price is not None and not actual.price_verified:
            action = MissionAction.SET_MANUAL_PRICE
            reason = "manual_price_not_independently_verified"
            data = dict(price=plan.manual_unit_price, warnings=plan.warnings,
                        missing=plan.pending)
        else:
            continue

        if action in {
            MissionAction.WRITE_DESCRIPTION, MissionAction.INSERT_IMAGE,
            MissionAction.SET_MANUAL_PRICE,
        } and scene.active_position_id != task.position_id:
            return MissionIntent(
                MissionAction.OBSERVE, task.position_id,
                "activate_exact_position_before_editing",
                proposed_route=plan.route, warnings=plan.warnings, missing=plan.pending,
            )

        # The caller must re-observe or escalate after no-progress. One
        # repeated attempt is not evidence and never implies task completion.
        attempt_id = task.position_id + ":" + action.value
        if attempt_id in attempted_without_progress:
            return MissionIntent(MissionAction.REVIEW, task.position_id,
                                 "action_repeated_without_progress:" + action.value,
                                 warnings=plan.warnings, missing=plan.pending)
        return MissionIntent(action, task.position_id, reason,
                             requires_v2_executor=True, **data)

    pending_prices = [
        task.position_id for task in tasks
        if task.allow_unpriced_draft
        and not _trusted_readback(task, scene, readbacks).price_verified
    ]
    if pending_prices:
        return MissionIntent(
            MissionAction.COMPLETE, None,
            "draft_partially_prepared_unpriced_positions",
            missing=tuple("price_unverified:" + p for p in pending_prices),
            verified_completed=False,
        )
    return MissionIntent(MissionAction.COMPLETE, None,
                         "all_required_position_fields_verified_for_quotation_draft",
                         verified_completed=True)


def mission_progress_summary(tasks: tuple[PositionTask, ...],
                             scene: MissionScene,
                             readbacks: tuple[PositionReadback, ...] = ()) -> dict:
    """Per-position factual progress, not a claim of save, warranty or production."""
    result = []
    for task in tasks:
        plan = plan_commercial_quote(task.request, scene.quote_capabilities, task.technical)
        actual = _trusted_readback(task, scene, readbacks)
        required = ["created", "description"]
        if task.request.image_reference:
            required.append("image")
        required.append("price")
        checks = {
            "created": actual.created_verified,
            "description": actual.description_verified,
            "image": actual.image_verified,
            "price": actual.price_verified,
        }
        result.append({
            "position_id": task.position_id,
            "route": plan.route.value,
            "verified": {key: checks[key] for key in required},
            "quotation_position_complete": all(checks[k] for k in required)
                                         and plan.route != QuoteRoute.MANUAL_REVIEW
                                         and not (task.request.manual_unit_price is not None
                                                  and plan.manual_unit_price is None),
            "warnings": list(plan.warnings),
            "pending": list(dict.fromkeys(
                list(plan.pending)
                + (["price_unverified_requires_salesperson"] if (
                    task.allow_unpriced_draft and not actual.price_verified
                ) else [])
            )),
            "price_status": (
                "verified" if actual.price_verified else
                "deferred_unverified" if task.allow_unpriced_draft else
                "unverified"
            ),
        })
    return {
        "document": scene.document_id if scene.document_identity_verified else None,
        "positions": result,
        "all_position_requirements_verified": bool(result) and all(
            item["quotation_position_complete"] for item in result
        ),
        "draft_positions_prepared": sum(
            bool(item["verified"].get("created"))
            and bool(item["verified"].get("description"))
            for item in result
        ),
        "unpriced_position_ids": [
            item["position_id"] for item in result
            if item["price_status"] == "deferred_unverified"
        ],
        "ready_for_final_customer_quote": bool(result) and all(
            item["quotation_position_complete"] for item in result
        ),
        "agent_authorized_to_save": False,
        "agent_authorized_to_send": False,
        "production_approval": False,
    }
