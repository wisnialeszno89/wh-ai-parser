from __future__ import annotations

import pytest

from app.agent.offers.drawing_offer_specification_builder import (
    DrawingOfferSpecificationBuilder,
    ReviewedDrawingPosition,
)
from app.agent.offers.drawing_position_extractor import (
    DrawingPositionCandidate,
    DrawingPositionExtractionResult,
)
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.drawing_quote_task import (
    create_drawing_offer_task_checkpoint,
)
from app.agent.runtime.resumable_task import TaskStatus
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository
from app.agent.runtime.resumable_task_service import ResumableTaskService
from app.wh.domain.offer.window_requirement import WindowRequirement


def reviewed_specification():
    rows = (
        (1, 4, 1120, 1440),
        (2, 2, 1100, 1440),
        (3, 2, 700, 1440),
        (4, 1, 2200, 1440),
        (5, 1, 1050, 2170),
        (6, 1, 2200, 1440),
    )
    extraction = DrawingPositionExtractionResult(
        source_alias="customer-drawing.jpg",
        page_number=1,
        positions=tuple(
            DrawingPositionCandidate(
                source_alias="customer-drawing.jpg",
                page_number=1,
                position_number=number,
                quantity=quantity,
                width_mm=width,
                height_mm=height,
                confidence=0.99,
                quantity_evidence=f"Menge {quantity}",
                width_evidence=str(width),
                height_evidence=str(height),
            )
            for number, quantity, width, height in rows
        ),
    )
    return DrawingOfferSpecificationBuilder().build(
        extraction,
        reviewed_positions=tuple(
            ReviewedDrawingPosition(number, width, height, quantity, True)
            for number, quantity, width, height in rows
        ),
        expected_position_numbers=tuple(range(1, 7)),
        review_confirmed=True,
        customer_name="Example Customer",
        language="de",
        notes="Visually reviewed customer drawing.",
    )


def test_drawing_quote_checkpoint_preserves_all_reviewed_positions():
    result = reviewed_specification()
    checkpoint = create_drawing_offer_task_checkpoint(
        result,
        task_id="drawing-six-window-test",
    )

    assert checkpoint.status is TaskStatus.WAITING_FOR_APPROVAL
    assert checkpoint.draft_only is True
    assert checkpoint.approval_required is True
    assert checkpoint.execution_approved is False
    assert checkpoint.expected_application == "WindowHub"
    assert checkpoint.facts["product_type"] == "window"
    assert checkpoint.facts["position_count"] == 6
    assert checkpoint.facts["total_quantity"] == 11
    assert checkpoint.facts["customer_name"] == "Example Customer"
    assert checkpoint.required_fields == (
        "product_type", "windows", "position_count", "total_quantity"
    )
    assert [
        (
            row["position_number"],
            row["width_mm"],
            row["height_mm"],
            row["quantity"],
            row["human_confirmed"],
        )
        for row in checkpoint.facts["windows"]
    ] == [
        (1, 1120, 1440, 4, True),
        (2, 1100, 1440, 2, True),
        (3, 700, 1440, 2, True),
        (4, 2200, 1440, 1, True),
        (5, 1050, 2170, 1, True),
        (6, 2200, 1440, 1, True),
    ]
    assert len(checkpoint.citations) == 18
    assert all(citation["source"]["human_confirmed"] is True for citation in checkpoint.citations)
    assert all(citation["source"]["source_alias"] == "customer-drawing.jpg" for citation in checkpoint.citations)


def test_checkpoint_rejects_specification_mutated_after_human_review():
    result = reviewed_specification()
    result.specification.windows[0].width = 999

    with pytest.raises(ValueError, match="does not match its human-reviewed values"):
        create_drawing_offer_task_checkpoint(result, task_id="mutated-drawing")


def test_checkpoint_rejects_non_human_confirmed_position():
    result = reviewed_specification()
    original = result.positions[0]
    result.positions = (  # type: ignore[misc]
        ReviewedDrawingPosition(
            original.position_number,
            original.width_mm,
            original.height_mm,
            original.quantity,
            False,
        ),
        *result.positions[1:],
    )

    with pytest.raises(ValueError, match="not been explicitly confirmed"):
        create_drawing_offer_task_checkpoint(result, task_id="unreviewed-drawing")


def test_agent_runtime_persists_drawing_checkpoint_without_observing_windowhub(tmp_path):
    observations = {"count": 0}

    def runner_factory(_checkpoint):
        raise AssertionError("Checkpoint creation must not construct a GUI runner.")

    service = ResumableTaskService(
        repository=TaskCheckpointRepository(tmp_path),
        runner_factory=runner_factory,
    )
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        resumable_task_service=service,
    )

    started = runtime.start_drawing_offer_task(
        reviewed_specification(),
        task_id="multi-window-approval-gate",
    )

    assert started.task_created is True
    assert started.requires_manual_review is True
    assert started.checkpoint.status is TaskStatus.WAITING_FOR_APPROVAL
    assert started.checkpoint.execution_approved is False
    assert started.checkpoint.actions_used == 0
    assert started.checkpoint.steps == ()
    assert observations["count"] == 0

    stored = runtime.get_resumable_task("multi-window-approval-gate")
    assert stored is not None
    assert stored.facts["position_count"] == 6
    assert stored.facts["total_quantity"] == 11
    assert stored.status is TaskStatus.WAITING_FOR_APPROVAL

    payload = started.to_payload()
    assert payload["windowhub_actions_executed"] == 0
    assert payload["offer_saved"] is False
    assert payload["offer_submitted"] is False


def test_checkpoint_serialization_round_trips_all_window_rows(tmp_path):
    service = ResumableTaskService(
        repository=TaskCheckpointRepository(tmp_path),
        runner_factory=lambda _checkpoint: (_ for _ in ()).throw(
            AssertionError("No runner is needed to store a checkpoint.")
        ),
    )
    checkpoint = create_drawing_offer_task_checkpoint(
        reviewed_specification(),
        task_id="roundtrip-drawing",
    )

    service.create(checkpoint)
    restored = service.get("roundtrip-drawing")

    assert restored is not None
    assert restored.to_payload() == checkpoint.to_payload()
    assert len(restored.facts["windows"]) == 6
    assert restored.approval_required is True
    assert restored.execution_approved is False
