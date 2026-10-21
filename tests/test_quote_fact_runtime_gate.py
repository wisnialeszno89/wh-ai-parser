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
    PdfDocumentExtraction,
    PdfPageFinding,
)
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

