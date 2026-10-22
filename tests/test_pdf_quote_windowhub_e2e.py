from __future__ import annotations

from types import SimpleNamespace

from app.agent.adapters.pdf_document_adapter import PdfDocumentAdapter
from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.resumable_task import TaskStatus
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository
from app.agent.session.agent_session_store import AgentSessionStore
from tests.test_pdf_document_adapter import write_text_pdf
from tests.test_windowhub_resumable_task_host import FakeElement, FakeScene


class SimulatedPdfQuoteWindowHubControl:
    """Stateful WindowHub scene fixture; never talks to a real desktop."""

    def __init__(self):
        self.scene = FakeScene([FakeElement("button", "Nowa oferta")])
        self.executed_targets: list[str] = []
        self.observe_count = 0

    def observe_scene(self):
        self.observe_count += 1
        return self.scene

    def run(self, *, plan, context):
        action = plan.steps[0].action
        matches = [
            element for element in self.scene.elements
            if element.label.casefold() == action.target.casefold()
        ]
        if len(matches) != 1:
            return SimpleNamespace(
                success=False,
                requires_manual_review=True,
                stopped=True,
                executed_actions=0,
                last_execution_result=None,
            )

        self.executed_targets.append(action.target)
        target = matches[0]

        if action.name == "click_screen_element" and action.target == "Nowa oferta":
            self.scene.active_document = "Oferta robocza"
            self.scene.elements = [
                FakeElement(
                    "button",
                    "Dodaj artykuł do konstrukcji",
                    metadata={"document_scope": "Oferta robocza"},
                ),
            ]
        elif action.name == "click_screen_element" and action.target == "Dodaj artykuł do konstrukcji":
            self.scene.elements = [
                FakeElement("list_item", "Okno", metadata={"uia_selected": False, "uia_owned_modal": True}),
                FakeElement("list_item", "Drzwi", metadata={"uia_selected": False, "uia_owned_modal": True}),
                FakeElement("button", "OK", metadata={"uia_owned_modal": True}),
                FakeElement("button", "Anuluj", metadata={"uia_owned_modal": True}),
            ]
        elif action.name == "click_screen_element" and action.target in {"Okno", "Drzwi"}:
            target.metadata = {**target.metadata, "uia_selected": True}
        elif action.name == "click_screen_element" and action.target == "OK":
            selected = next(
                element.label
                for element in self.scene.elements
                if element.label in {"Okno", "Drzwi"}
                and element.metadata.get("uia_selected") is True
            )
            self.scene.elements = [
                FakeElement(
                    "list_item",
                    selected,
                    metadata={
                        "uia_selected": True,
                        "document_scope": "Oferta robocza",
                    },
                ),
                FakeElement(
                    "edit",
                    "Ilość",
                    "writable",
                    metadata={"current_value": "", "document_scope": "Oferta robocza"},
                ),
                FakeElement(
                    "edit",
                    "Szerokość",
                    "writable",
                    metadata={"current_value": "", "document_scope": "Oferta robocza"},
                ),
                FakeElement(
                    "edit",
                    "Wysokość",
                    "writable",
                    metadata={"current_value": "", "document_scope": "Oferta robocza"},
                ),
                FakeElement(
                    "button",
                    "Zapisz szkic",
                    metadata={"document_scope": "Oferta robocza"},
                ),
            ]
        elif action.name == "write_text":
            target.metadata = {
                **target.metadata,
                "current_value": action.value,
            }
        elif action.name == "click_screen_element" and action.target == "Zapisz szkic":
            self.scene.elements.append(
                FakeElement(
                    "text",
                    "Szkic zapisany",
                    metadata={"document_scope": "Oferta robocza"},
                )
            )

        raw = SimpleNamespace(
            success=True,
            message="simulated WindowHub action executed",
            metadata={
                "executed": True,
                "target": action.target,
                "execution_path": "simulated_pdf_quote_windowhub",
            },
        )
        attempt = SimpleNamespace(
            execution_result=raw,
            verification_result=SimpleNamespace(verified=False),
        )
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            stopped=False,
            executed_actions=1,
            last_execution_result=SimpleNamespace(last_attempt=attempt),
        )


class SimulatedPdfQuotePlanner:
    """Deterministic test planner matching actions to the supplied PDF facts."""

    def __init__(self, *, choose_wrong_product: bool = False):
        self.choose_wrong_product = choose_wrong_product
        self.application_knowledge = None

    def prepare(
        self,
        request,
        initial_scene=None,
        application_knowledge=None,
        autonomous=False,
        reasoning_budget=None,
    ):
        self.application_knowledge = application_knowledge
        labels = {element.label: element for element in initial_scene.elements}
        action = None

        if "Nowa oferta" in labels:
            action = AgentAction(
                name="click_screen_element",
                description="Open a new draft offer.",
                target="Nowa oferta",
            )
        elif "Dodaj artykuł do konstrukcji" in labels:
            action = AgentAction(
                name="click_screen_element",
                description="Open the product selector.",
                target="Dodaj artykuł do konstrukcji",
            )
        elif "Okno" in labels and "Drzwi" in labels and "OK" in labels:
            selected = any(
                labels[name].metadata.get("uia_selected") is True
                for name in ("Okno", "Drzwi")
            )
            if selected:
                target = "OK"
            elif self.choose_wrong_product:
                target = "Drzwi"
            else:
                target = "Okno"
            action = AgentAction(
                name="click_screen_element",
                description="Choose the product type specified by the validated facts.",
                target=target,
            )
        elif "Ilość" in labels and not labels["Ilość"].metadata.get("current_value"):
            action = AgentAction(
                name="write_text",
                description="Enter the validated quantity.",
                target="Ilość",
                value="2",
            )
        elif "Szerokość" in labels and not labels["Szerokość"].metadata.get("current_value"):
            action = AgentAction(
                name="write_text",
                description="Enter the validated width.",
                target="Szerokość",
                value="1200",
            )
        elif "Wysokość" in labels and not labels["Wysokość"].metadata.get("current_value"):
            action = AgentAction(
                name="write_text",
                description="Enter the validated height.",
                target="Wysokość",
                value="1500",
            )
        elif "Zapisz szkic" in labels and "Szkic zapisany" not in labels:
            action = AgentAction(
                name="click_screen_element",
                description="Save the draft, without submitting it.",
                target="Zapisz szkic",
            )
        elif "Szkic zapisany" in labels:
            return SimpleNamespace(
                request=request,
                intent=AgentIntent.CREATE_QUOTE,
                plan=ActionPlan(
                    intent=AgentIntent.CREATE_QUOTE,
                    steps=(),
                    confidence=1.0,
                    completed=True,
                ),
                requires_manual_review=False,
            )

        if action is None:
            return SimpleNamespace(
                request=request,
                intent=AgentIntent.CREATE_QUOTE,
                plan=None,
                requires_manual_review=True,
                get_value=lambda _key: "no_supported_next_action",
            )

        return SimpleNamespace(
            request=request,
            intent=AgentIntent.CREATE_QUOTE,
            plan=ActionPlan(
                intent=AgentIntent.CREATE_QUOTE,
                steps=(ActionStep(index=1, action=action),),
                confidence=1.0,
                requires_manual_review=False,
                completed=False,
            ),
            requires_manual_review=False,
        )


def make_runtime(tmp_path, *, choose_wrong_product: bool = False):
    approved_root = tmp_path / "approved"
    approved_root.mkdir()
    control = SimulatedPdfQuoteWindowHubControl()
    planner = SimulatedPdfQuotePlanner(choose_wrong_product=choose_wrong_product)
    runtime = AgentRuntime(
        orchestrator=planner,
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=control,
        pdf_ingestion_service=PdfIngestionService(
            adapter=PdfDocumentAdapter(allowed_roots=(approved_root,)),
        ),
    )
    repository = TaskCheckpointRepository(tmp_path / "task-checkpoints")
    runtime.configure_windowhub_resumable_tasks(repository=repository)
    return runtime, control, planner, approved_root, repository


def ingest_basic_quote(runtime, root, *, source_alias="quote-001"):
    source = root / "quote.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
            "Height: 1500 mm",
            "Quantity: 2 pcs",
        ],
    )
    runtime.ingest_pdf(source, source_alias=source_alias)


def advance_until_terminal(runtime, task_id):
    state = runtime.get_resumable_task(task_id)
    for _ in range(12):
        state = runtime.advance_resumable_task(task_id)
        if state.status in {
            TaskStatus.COMPLETED,
            TaskStatus.STOPPED,
            TaskStatus.WAITING_FOR_INPUT,
            TaskStatus.WAITING_FOR_CONFIRMATION,
            TaskStatus.WAITING_FOR_APPROVAL,
        }:
            return state
    return state


def test_pdf_quote_flows_through_approval_gated_windowhub_draft_simulation(tmp_path):
    runtime, control, planner, root, repository = make_runtime(tmp_path)
    ingest_basic_quote(runtime, root)

    started = runtime.start_pdf_quote_task(
        "quote-001",
        task_id="pdf-windowhub-draft-e2e",
        request_message="Prepare a draft offer using the supplied PDF.",
    )

    assert started.task_created is True
    assert started.checkpoint is not None
    assert started.checkpoint.status is TaskStatus.WAITING_FOR_APPROVAL
    assert set(started.checkpoint.required_fields) == {
        "product_type", "width", "height", "quantity"
    }
    assert control.observe_count == 0
    assert control.executed_targets == []

    waiting = runtime.advance_resumable_task("pdf-windowhub-draft-e2e")
    assert waiting.status is TaskStatus.WAITING_FOR_APPROVAL
    assert control.observe_count == 0
    assert control.executed_targets == []

    approved = runtime.approve_resumable_task_execution("pdf-windowhub-draft-e2e")
    assert approved.execution_approved is True
    assert approved.status is TaskStatus.READY

    final = advance_until_terminal(runtime, "pdf-windowhub-draft-e2e")

    assert final.status is TaskStatus.COMPLETED
    assert final.draft_only is True
    assert final.actions_used == 8
    assert control.executed_targets == [
        "Nowa oferta",
        "Dodaj artykuł do konstrukcji",
        "Okno",
        "OK",
        "Ilość",
        "Szerokość",
        "Wysokość",
        "Zapisz szkic",
    ]
    assert all(step.executed and step.execution_success and step.verified for step in final.completed_steps)
    assert {item["field"] for item in final.final_evidence} == {
        "product_type", "quantity", "width", "height"
    }
    assert final.final_evidence[0]["verification"] == "selected_product_item"
    assert {item["source"]["page_number"] for item in final.citations} == {1, 2, 3, 4}
    assert planner.application_knowledge["application"] == "WindowHub"
    assert repository.get("pdf-windowhub-draft-e2e") == final
    assert all("Wyślij ofertę" not in target for target in control.executed_targets)


def test_pdf_quote_task_refuses_to_select_a_product_that_conflicts_with_source_fact(tmp_path):
    runtime, control, planner, root, repository = make_runtime(tmp_path, choose_wrong_product=True)
    ingest_basic_quote(runtime, root, source_alias="quote-wrong-product")

    started = runtime.start_pdf_quote_task(
        "quote-wrong-product",
        task_id="pdf-windowhub-wrong-product",
        request_message="Prepare a draft offer using the supplied PDF.",
    )
    assert started.task_created is True
    runtime.approve_resumable_task_execution("pdf-windowhub-wrong-product")

    waiting = advance_until_terminal(runtime, "pdf-windowhub-wrong-product")

    assert waiting.status is TaskStatus.WAITING_FOR_INPUT
    assert any("conflicts with the task's supplied product_type" in issue for issue in waiting.unresolved_issues)
    assert control.executed_targets == [
        "Nowa oferta",
        "Dodaj artykuł do konstrukcji",
    ]
    assert "Drzwi" not in control.executed_targets
    assert "Zapisz szkic" not in control.executed_targets
    assert repository.get("pdf-windowhub-wrong-product").draft_only is True
