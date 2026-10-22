from __future__ import annotations

from types import SimpleNamespace

from app.agent.adapters.pdf_document_adapter import PdfDocumentAdapter
from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.resumable_task import (
    Execution,
    PlanDecision,
    ResumableTaskRunner,
    TaskCheckpoint,
    TaskStatus,
    Verification,
)
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository
from app.agent.runtime.resumable_task_service import ResumableTaskService
from app.agent.session.agent_session_store import AgentSessionStore
from tests.test_pdf_document_adapter import write_text_pdf


def make_runtime(root, store_dir):
    observations = {"count": 0}

    def observe():
        observations["count"] += 1
        return SimpleNamespace(
            observation=SimpleNamespace(
                state=SimpleNamespace(
                    active_application="WindowHub",
                    active_window_title="WindowHub - New Offer",
                )
            ),
            active_document="New Offer",
            elements=(),
        )

    def plan_next(checkpoint, scene):
        return PlanDecision(complete=True)

    def execute_action(action, scene, validation):
        return Execution(False, False, "This simulated completion does not execute actions.")

    def verify_action(action, execution, scene):
        return Verification(False, reason="No action should be executed in this test.")

    def verify_final_state(checkpoint, scene):
        return Verification(
            True,
            evidence=(
                {
                    "verification": "simulated_final_state",
                    "task_id": checkpoint.task_id,
                    "draft_only": checkpoint.draft_only,
                },
            ),
        )

    repository = TaskCheckpointRepository(store_dir)
    resumable = ResumableTaskService(
        repository=repository,
        runner_factory=lambda checkpoint: ResumableTaskRunner(
            observe=observe,
            plan_next=plan_next,
            execute_action=execute_action,
            verify_action=verify_action,
            verify_final_state=verify_final_state,
        ),
    )
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        pdf_ingestion_service=PdfIngestionService(
            adapter=PdfDocumentAdapter(allowed_roots=(root,)),
        ),
        resumable_task_service=resumable,
    )
    return runtime, repository, observations


def test_valid_pdf_quote_creates_persisted_task_waiting_for_approval(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "offer.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
            "Height: 1500 mm",
            "Quantity: 2 pcs",
        ],
    )
    runtime, repository, observations = make_runtime(root, tmp_path / "checkpoints")
    runtime.ingest_pdf(source, source_alias="offer-001")

    started = runtime.start_pdf_quote_task(
        "offer-001",
        task_id="pdf-quote-test",
        request_message="Prepare a draft quote from the supplied PDF.",
        max_actions=6,
        max_reasoning_calls=6,
    )

    assert started.task_created is True
    assert started.requires_manual_review is False
    checkpoint = started.checkpoint
    assert checkpoint is not None
    assert checkpoint.status is TaskStatus.WAITING_FOR_APPROVAL
    assert checkpoint.approval_required is True
    assert checkpoint.execution_approved is False
    assert checkpoint.draft_only is True
    assert checkpoint.expected_application == "WindowHub"
    assert checkpoint.facts["product_type"] == "window"
    assert checkpoint.facts["width"] == 1200
    assert checkpoint.facts["height"] == 1500
    assert checkpoint.facts["quantity"] == 2
    assert {c["field_name"] for c in checkpoint.citations} >= {
        "product_type", "width", "height", "quantity"
    }
    assert all("evidence_text" in c for c in checkpoint.citations)
    assert observations["count"] == 0

    # Checkpoints are locally persisted and keep the task gate after reload.
    stored = repository.get("pdf-quote-test")
    assert stored is not None
    assert stored.status is TaskStatus.WAITING_FOR_APPROVAL
    assert stored.approval_required is True
    assert stored.execution_approved is False
    assert "request_message" not in stored.facts
    assert str(root) not in str(stored.to_payload())


def test_advance_cannot_observe_or_act_before_explicit_task_approval(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "offer.pdf"
    write_text_pdf(source, ["Product: window", "Width: 1200 mm", "Height: 1500 mm"])
    runtime, repository, observations = make_runtime(root, tmp_path / "checkpoints")
    runtime.ingest_pdf(source, source_alias="offer-002")
    started = runtime.start_pdf_quote_task(
        "offer-002",
        task_id="approval-gate-test",
        request_message="Prepare a draft quote.",
    )
    assert started.checkpoint is not None

    first_advance = runtime.advance_resumable_task("approval-gate-test")

    assert first_advance.status is TaskStatus.WAITING_FOR_APPROVAL
    assert first_advance.execution_approved is False
    assert observations["count"] == 0

    approved = runtime.approve_resumable_task_execution("approval-gate-test")

    assert approved.status is TaskStatus.READY
    assert approved.execution_approved is True
    assert approved.approval_required is True

    completed = runtime.advance_resumable_task("approval-gate-test")

    assert completed.status is TaskStatus.COMPLETED
    assert completed.draft_only is True
    assert observations["count"] == 1
    assert completed.actions_used == 0
    assert completed.final_evidence[0]["verification"] == "simulated_final_state"
    assert repository.get("approval-gate-test").status is TaskStatus.COMPLETED


def test_incomplete_or_ocr_required_pdf_creates_no_resumable_task(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    incomplete_path = root / "incomplete.pdf"
    write_text_pdf(incomplete_path, ["Product: window", "Width: 1200 mm"])
    runtime, repository, observations = make_runtime(root, tmp_path / "checkpoints")
    runtime.ingest_pdf(incomplete_path, source_alias="incomplete")

    incomplete = runtime.start_pdf_quote_task(
        "incomplete",
        task_id="blocked-incomplete",
        request_message="Prepare a draft quote.",
    )

    assert incomplete.task_created is False
    assert incomplete.requires_manual_review is True
    assert incomplete.checkpoint is None
    assert incomplete.to_payload()["status"] == "manual_review"
    assert repository.get("blocked-incomplete") is None

    mixed_path = root / "mixed.pdf"
    write_text_pdf(
        mixed_path,
        ["Product: window", "Width: 1200 mm", "Height: 1500 mm", ""],
    )
    runtime.ingest_pdf(mixed_path, source_alias="mixed")
    mixed = runtime.start_pdf_quote_task(
        "mixed",
        task_id="blocked-ocr",
        request_message="Prepare a draft quote.",
    )

    assert mixed.task_created is False
    assert mixed.requires_manual_review is True
    assert mixed.preparation.extraction.ocr_required_pages == (4,)
    assert repository.get("blocked-ocr") is None
    assert observations["count"] == 0


def test_conflicting_pdf_dimensions_cannot_create_task_even_if_other_fields_exist(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "conflict.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
            "Width: 1300 mm",
            "Height: 1500 mm",
        ],
    )
    runtime, repository, observations = make_runtime(root, tmp_path / "checkpoints")
    runtime.ingest_pdf(source, source_alias="conflict")

    started = runtime.start_pdf_quote_task(
        "conflict",
        task_id="blocked-conflict",
        request_message="Prepare a draft quote.",
    )

    assert started.task_created is False
    assert started.requires_manual_review is True
    assert any(
        item.code == "conflicting_width"
        for item in started.preparation.validation.conflicts
    )
    assert repository.get("blocked-conflict") is None
    assert observations["count"] == 0


def test_task_approval_flags_round_trip_and_legacy_checkpoints_keep_defaults():
    gated = TaskCheckpoint(
        task_id="gated",
        goal="prepare draft",
        status=TaskStatus.WAITING_FOR_APPROVAL,
        approval_required=True,
        execution_approved=False,
    )
    restored = TaskCheckpoint.from_payload(gated.to_payload())
    assert restored.status is TaskStatus.WAITING_FOR_APPROVAL
    assert restored.approval_required is True
    assert restored.execution_approved is False

    legacy_payload = {
        "schema_version": 1,
        "task_id": "legacy",
        "goal": "existing task",
        "status": "ready",
    }
    legacy = TaskCheckpoint.from_payload(legacy_payload)
    assert legacy.approval_required is False
    assert legacy.execution_approved is False
