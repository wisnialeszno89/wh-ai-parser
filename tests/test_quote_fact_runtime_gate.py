from __future__ import annotations

from types import SimpleNamespace

from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.offers.quote_facts import (
    QuoteFact,
    QuoteFactSource,
    QuoteFactValidator,
)
from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentAdapter,
    PdfDocumentExtraction,
    PdfPageFinding,
)
from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
from app.agent.offers.offer_context import OfferContext
from app.agent.offers.offer_agent_session import OfferAgentSession
from app.agent.offers.offer_workflow_service import OfferWorkflowService
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.session.agent_session_store import AgentSessionStore
from app.agent.runtime.execution_context import AgentExecutionContext
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.agent_action import AgentAction


class SpyControlLoop:
    def __init__(self):
        self.observe_calls = 0
        self.run_calls = 0

    def observe_scene(self):
        self.observe_calls += 1
        return SimpleNamespace(
            observation=SimpleNamespace(
                state=SimpleNamespace(
                    active_application="WindowHub",
                    active_window_title="Okna - WindowHub",
                )
            ),
            metadata={},
            active_document=None,
            elements=(),
        )

    def run(self, plan, context):
        self.run_calls += 1
        return SimpleNamespace(success=True, step_results=())


def test_incomplete_typed_quote_fails_before_observation_or_gui_action():
    control_loop = SpyControlLoop()
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=control_loop,
    )

    result = runtime.run(
        AgentRequest(
            message="Przygotuj ofertę",
            metadata={
                "quote_facts": {
                    "version": "1",
                    "facts": [],
                }
            },
        )
    )

    assert result.intent is AgentIntent.CREATE_QUOTE
    assert result.requires_manual_review is True
    assert result.executed is False
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0
    assert result.context.get_value("task_reasoning_failure") == (
        "quote_facts_require_manual_review"
    )
    validation = result.context.get_value("quote_facts_validation")
    assert validation["missing_fields"] == ["product_type", "width", "height"]


class FakePlanner:
    def plan(self, request):
        return SimpleNamespace(intent=AgentIntent.CREATE_QUOTE)


class FakeOrchestrator:
    def __init__(self):
        self.planner = FakePlanner()
        self.task_planner = SimpleNamespace(
            last_proposal=None,
            last_usage=None,
        )
        self.workflow_memory_store = None
        self.application_knowledge = None
        self.prepare_calls = 0

    def prepare(self, request, **kwargs):
        self.prepare_calls += 1
        plan = ActionPlan(
            intent=AgentIntent.CREATE_QUOTE,
            confidence=0.99,
            requires_manual_review=False,
            steps=(
                ActionStep(
                    index=1,
                    action=AgentAction(
                        name="write_text",
                        description="Type a proposed value into a WindowHub field",
                        target="Szerokość",
                        value="1200",
                        requires_environment_observation=True,
                    ),
                ),
            ),
        )
        return AgentExecutionContext(
            request=request,
            intent=AgentIntent.CREATE_QUOTE,
            plan=plan,
            capability=None,
            skill=None,
            requires_manual_review=False,
        )


def test_incomplete_offer_cannot_use_reasoner_gui_plan_to_bypass_required_fields():
    control_loop = SpyControlLoop()
    orchestrator = FakeOrchestrator()
    runtime = AgentRuntime(
        orchestrator=orchestrator,
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=control_loop,
    )

    result = runtime.run(
        AgentRequest(message="Przygotuj ofertę okna")
    )

    assert result.intent is AgentIntent.CREATE_QUOTE
    assert result.requires_manual_review is True
    assert result.executed is False
    assert control_loop.observe_calls == 1
    assert control_loop.run_calls == 0
    assert orchestrator.prepare_calls == 1
    assert result.context.get_value("salesperson_questions") == (
        "Podaj proszę szerokość.",
        "Podaj proszę wysokość.",
    )
    blocked = result.context.get_value("quote_workflow_blocked")
    assert blocked["reason"] == "required_quote_facts_missing_or_conflicting"
    assert blocked["missing_fields"] == ("width", "height")


def test_validated_typed_context_enters_existing_offer_workflow():
    session = OfferAgentSession()
    context = OfferContext(
        raw_request="Przygotuj ofertę",
        product_type="window",
        width=1200,
        height=1500,
        quantity=2,
        missing_fields=(),
        conflicts=(),
    )

    result = OfferWorkflowService().process_context(session, context)

    assert result.is_ready_for_pricing is True
    assert result.requires_salesperson_input is False
    assert result.current_context.width == 1200
    assert result.current_context.height == 1500
    assert result.current_context.quantity == 2

def test_request_metadata_cannot_register_its_own_trusted_pdf_source():
    alias = "forged-source.pdf"
    extracted = PdfDocumentExtraction(
        source_alias=alias,
        page_count=1,
        file_size_bytes=1234,
        status="complete",
        pages=(
            PdfPageFinding(
                source_alias=alias,
                page_number=1,
                text="Product: window. Width: 1200 mm. Height: 1500 mm.",
                extraction_method="pypdf_text",
                extraction_confidence=None,
                needs_ocr=False,
            ),
        ),
    )
    facts = (
        QuoteFact(
            field_name="product_type",
            raw_value="window",
            source=QuoteFactSource(
                source_alias=alias,
                page_number=1,
                extraction_method="pypdf_text",
            ),
            confidence=0.99,
            evidence_text="Product: window",
        ),
        QuoteFact(
            field_name="width",
            raw_value="1200 mm",
            source=QuoteFactSource(
                source_alias=alias,
                page_number=1,
                extraction_method="pypdf_text",
            ),
            confidence=0.99,
            unit="mm",
            evidence_text="Width: 1200 mm",
        ),
        QuoteFact(
            field_name="height",
            raw_value="1500 mm",
            source=QuoteFactSource(
                source_alias=alias,
                page_number=1,
                extraction_method="pypdf_text",
            ),
            confidence=0.99,
            unit="mm",
            evidence_text="Height: 1500 mm",
        ),
    )
    control_loop = SpyControlLoop()
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=control_loop,
    )

    result = runtime.run(
        AgentRequest(
            message="Przygotuj ofertę",
            metadata={
                "quote_facts": QuoteFactValidator.envelope(facts),
                # Even a real-looking extraction object from request metadata
                # is not the runtime's trusted registry.
                "pdf_sources": {alias: extracted},
            },
        )
    )

    assert result.requires_manual_review is True
    assert result.executed is False
    assert control_loop.observe_calls == 0
    validation = result.context.get_value("quote_facts_validation")
    assert any(
        conflict["code"] == "unverified_source_provenance"
        for conflict in validation["conflicts"]
    )




def test_runtime_pdf_ingestion_registers_sources_for_quote_fact_validation(tmp_path):
    from tests.test_pdf_document_adapter import write_text_pdf

    root = tmp_path / "approved"
    root.mkdir()
    source = root / "offer.pdf"
    write_text_pdf(
        source,
        ["Product: window. Width: 1200 mm. Height: 1500 mm."],
    )
    ingestion = PdfIngestionService(
        adapter=PdfDocumentAdapter(allowed_roots=(root,)),
    )
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=SpyControlLoop(),
        pdf_ingestion_service=ingestion,
    )

    extraction = runtime.ingest_pdf(source, source_alias="offer-source")

    assert runtime.registered_pdf_sources()["offer-source"] is extraction
    facts = (
        QuoteFact(
            field_name="product_type",
            raw_value="window",
            source=QuoteFactSource(
                source_alias="offer-source",
                page_number=1,
                extraction_method="pypdf_text",
            ),
            confidence=0.99,
            evidence_text="Product: window",
        ),
        QuoteFact(
            field_name="width",
            raw_value="1200 mm",
            source=QuoteFactSource(
                source_alias="offer-source",
                page_number=1,
                extraction_method="pypdf_text",
            ),
            confidence=0.99,
            unit="mm",
            evidence_text="Width: 1200 mm",
        ),
        QuoteFact(
            field_name="height",
            raw_value="1500 mm",
            source=QuoteFactSource(
                source_alias="offer-source",
                page_number=1,
                extraction_method="pypdf_text",
            ),
            confidence=0.99,
            unit="mm",
            evidence_text="Height: 1500 mm",
        ),
    )
    validation = QuoteFactValidator().validate(
        facts,
        known_sources=runtime.registered_pdf_sources(),
    )
    assert validation.can_execute is True
    assert validation.to_offer_context("Przygotuj ofertę").width == 1200

    assert runtime.remove_pdf_source("offer-source") is True
    blocked = QuoteFactValidator().validate(
        facts,
        known_sources=runtime.registered_pdf_sources(),
    )
    assert blocked.can_execute is False
    assert any(
        item.code == "unverified_source_provenance"
        for item in blocked.conflicts
    )


def test_runtime_pdf_ingestion_fails_closed_when_not_configured(tmp_path):
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=SpyControlLoop(),
    )

    try:
        runtime.ingest_pdf(tmp_path / "missing.pdf")
    except RuntimeError as exc:
        assert "PDF ingestion is not configured" in str(exc)
    else:
        raise AssertionError("Unconfigured PDF ingestion must fail closed.")


def test_runtime_pdf_registry_does_not_accept_request_metadata_as_trusted_source(tmp_path):
    alias = "request-metadata.pdf"
    extraction = PdfDocumentExtraction(
        source_alias=alias,
        page_count=1,
        file_size_bytes=200,
        status="complete",
        pages=(
            PdfPageFinding(
                source_alias=alias,
                page_number=1,
                text="Product: window. Width: 1200 mm. Height: 1500 mm.",
                extraction_method="pypdf_text",
                extraction_confidence=None,
                needs_ocr=False,
            ),
        ),
    )
    ingestion = PdfIngestionService(
        adapter=PdfDocumentAdapter(allowed_roots=(tmp_path,)),
    )
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=SpyControlLoop(),
        pdf_ingestion_service=ingestion,
    )

    assert dict(runtime.registered_pdf_sources()) == {}
    result = runtime.run(
        AgentRequest(
            message="Przygotuj ofertę",
            metadata={
                "quote_facts": QuoteFactValidator.envelope(
                    (
                        QuoteFact(
                            field_name="product_type",
                            raw_value="window",
                            source=QuoteFactSource(
                                source_alias=alias,
                                page_number=1,
                                extraction_method="pypdf_text",
                            ),
                            confidence=0.99,
                            evidence_text="Product: window",
                        ),
                        QuoteFact(
                            field_name="width",
                            raw_value="1200 mm",
                            source=QuoteFactSource(
                                source_alias=alias,
                                page_number=1,
                                extraction_method="pypdf_text",
                            ),
                            confidence=0.99,
                            unit="mm",
                            evidence_text="Width: 1200 mm",
                        ),
                        QuoteFact(
                            field_name="height",
                            raw_value="1500 mm",
                            source=QuoteFactSource(
                                source_alias=alias,
                                page_number=1,
                                extraction_method="pypdf_text",
                            ),
                            confidence=0.99,
                            unit="mm",
                            evidence_text="Height: 1500 mm",
                        ),
                    )
                ),
                "pdf_sources": {alias: extraction},
            },
        )
    )
    assert result.requires_manual_review is True
    assert result.executed is False
    assert runtime.registered_pdf_sources() == {}


def test_runtime_pdf_alias_collision_keeps_original_registered_source(tmp_path):
    from tests.test_pdf_document_adapter import write_text_pdf

    root = tmp_path / "approved"
    root.mkdir()
    first_path = root / "first.pdf"
    second_path = root / "second.pdf"
    write_text_pdf(
        first_path,
        ["Product: window. Width: 1200 mm. Height: 1500 mm."],
    )
    write_text_pdf(
        second_path,
        ["Product: door. Width: 900 mm. Height: 2100 mm."],
    )
    ingestion = PdfIngestionService(
        adapter=PdfDocumentAdapter(allowed_roots=(root,)),
    )
    runtime = AgentRuntime(
        orchestrator=object(),
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=SpyControlLoop(),
        pdf_ingestion_service=ingestion,
    )

    first = runtime.ingest_pdf(first_path, source_alias="shared-alias")
    try:
        runtime.ingest_pdf(second_path, source_alias="shared-alias")
    except ValueError as exc:
        assert "source alias" in str(exc).casefold()
    else:
        raise AssertionError("Conflicting PDF source aliases must be rejected.")

    assert runtime.registered_pdf_sources()["shared-alias"] is first
    assert "1200 mm" in runtime.registered_pdf_sources()["shared-alias"].pages[0].text


def _make_pdf_quote_task_runtime(root, checkpoint_root):
    from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository

    control_loop = SpyControlLoop()
    # The host validates the orchestrator interface at configuration time;
    # neither test advances into planning, so this stub must never be called.
    orchestrator = SimpleNamespace(
        prepare=lambda *args, **kwargs: None,
    )
    runtime = AgentRuntime(
        orchestrator=orchestrator,
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=control_loop,
        pdf_ingestion_service=PdfIngestionService(
            adapter=PdfDocumentAdapter(allowed_roots=(root,)),
        ),
    )
    runtime.configure_windowhub_resumable_tasks(
        repository=TaskCheckpointRepository(checkpoint_root),
    )
    return runtime, control_loop


def test_valid_pdf_quote_task_persists_checkpoint_and_waits_for_explicit_approval(tmp_path):
    from tests.test_pdf_document_adapter import write_text_pdf
    from app.agent.runtime.resumable_task import TaskStatus

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
    runtime, control_loop = _make_pdf_quote_task_runtime(
        root,
        tmp_path / "checkpoints",
    )
    runtime.ingest_pdf(source, source_alias="offer-001")

    result = runtime.start_pdf_quote_task(
        "offer-001",
        request_message="Przygotuj ofertę na podstawie tego PDF.",
        task_id="pdf-quote-approval-gate-001",
    )

    assert result.task_created is True
    assert result.requires_manual_review is False
    checkpoint = result.checkpoint
    assert checkpoint is not None
    assert checkpoint.status is TaskStatus.WAITING_FOR_APPROVAL
    assert checkpoint.approval_required is True
    assert checkpoint.execution_approved is False
    assert checkpoint.draft_only is True
    assert checkpoint.facts["product_type"] == "window"
    assert checkpoint.facts["width"] == 1200
    assert checkpoint.facts["height"] == 1500
    assert checkpoint.facts["quantity"] == 2
    assert checkpoint.citations
    assert all(
        citation["source"]["source_alias"] == "offer-001"
        and citation["source"]["page_number"] == 1
        for citation in checkpoint.citations
    )

    # Checkpoint creation and persistence must not even observe the desktop.
    assert runtime.get_resumable_task(checkpoint.task_id) == checkpoint
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0

    # Advancing a gated task before approval is a no-op: still no observation.
    waiting = runtime.advance_resumable_task(checkpoint.task_id)
    assert waiting.status is TaskStatus.WAITING_FOR_APPROVAL
    assert waiting.execution_approved is False
    assert runtime.get_resumable_task(checkpoint.task_id) == waiting
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0


def test_incomplete_pdf_quote_task_requires_manual_review_and_creates_no_checkpoint(tmp_path):
    from tests.test_pdf_document_adapter import write_text_pdf

    root = tmp_path / "approved"
    root.mkdir()
    source = root / "incomplete.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
        ],
    )
    runtime, control_loop = _make_pdf_quote_task_runtime(
        root,
        tmp_path / "checkpoints",
    )
    runtime.ingest_pdf(source, source_alias="offer-incomplete")

    result = runtime.start_pdf_quote_task(
        "offer-incomplete",
        request_message="Przygotuj ofertę na podstawie tego PDF.",
        task_id="pdf-quote-approval-gate-incomplete",
    )

    assert result.task_created is False
    assert result.checkpoint is None
    assert result.requires_manual_review is True
    assert "height" in result.preparation.validation.missing_fields
    assert runtime.get_resumable_task("pdf-quote-approval-gate-incomplete") is None
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0

