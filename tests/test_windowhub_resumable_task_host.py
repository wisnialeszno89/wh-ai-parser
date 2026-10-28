from dataclasses import dataclass, field
from types import SimpleNamespace

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.resumable_task import TaskAction, TaskCheckpoint, TaskStatus, Verification
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository
from app.agent.runtime.windowhub_resumable_task_host import (
    WindowHubResumableTaskHost,
    verify_windowhub_final_state,
)


@dataclass
class FakeElement:
    kind: str
    label: str
    interaction_capability: str = "clickable"
    confidence: float = 0.99
    metadata: dict = field(default_factory=dict)


@dataclass
class FakeScene:
    elements: list[FakeElement]
    active_document: str | None = None
    metadata: dict = field(default_factory=dict)
    observation: object = field(default_factory=lambda: SimpleNamespace(
        state=SimpleNamespace(
            active_application="WindowHub",
            active_window_title="Okna - Oferta",
        ),
        metadata={},
    ))


class SimulatedWindowHubControlLoop:
    """Stateful UI fixture; no OS UI, screenshots, coordinates or network."""

    def __init__(self):
        self.scene = FakeScene([FakeElement("button", "Nowa oferta")])
        self.executed_targets = []
        self.observe_calls = 0

    def observe_scene(self):
        self.observe_calls += 1
        return self.scene

    def run(self, *, plan, context):
        action = plan.steps[0].action
        matches = [e for e in self.scene.elements if e.label.casefold() == action.target.casefold()]
        if len(matches) != 1:
            return SimpleNamespace(
                success=False, requires_manual_review=True, stopped=True,
                executed_actions=0, last_execution_result=None,
            )
        self.executed_targets.append(action.target)

        if action.name == "click_screen_element" and action.target == "Nowa oferta":
            self.scene.active_document = "Oferta robocza"
            self.scene.elements = [
                FakeElement("edit", "Szerokość", "writable", metadata={
                    "current_value": "", "document_scope": "Oferta robocza"
                }),
                FakeElement("edit", "Wysokość", "writable", metadata={
                    "current_value": "", "document_scope": "Oferta robocza"
                }),
                FakeElement("button", "Zapisz szkic", metadata={
                    "document_scope": "Oferta robocza"
                }),
            ]
        elif action.name == "write_text":
            target = matches[0]
            target.metadata = {**target.metadata, "current_value": action.value}
        elif action.name == "click_screen_element" and action.target == "Zapisz szkic":
            self.scene.elements = [
                *self.scene.elements,
                FakeElement("text", "Szkic zapisany", metadata={
                    "document_scope": "Oferta robocza"
                }),
            ]
        elif action.name == "click_screen_element" and action.target == "Wyślij ofertę":
            self.scene.elements = [FakeElement("text", "Wysłano", metadata={
                "document_scope": "Oferta robocza"
            })]

        raw = SimpleNamespace(
            success=True,
            message="simulated action executed",
            metadata={"executed": True, "target": action.target, "execution_path": "fake_windowhub"},
        )
        attempt = SimpleNamespace(execution_result=raw, verification_result=None)
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            stopped=False,
            executed_actions=1,
            last_execution_result=SimpleNamespace(last_attempt=attempt),
        )


class SimulatedOfferOrchestrator:
    def __init__(self, *, wrong_width=False, submit=False):
        self.wrong_width = wrong_width
        self.submit = submit
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
        scene = initial_scene
        labels = {e.label: e for e in scene.elements}
        action = None

        if self.submit:
            if "Wyślij ofertę" in labels:
                action = AgentAction(
                    name="click_screen_element",
                    description="Submit the offer only after explicit approval.",
                    target="Wyślij ofertę",
                )
            else:
                plan = ActionPlan(
                    intent=AgentIntent.CREATE_QUOTE,
                    steps=(),
                    confidence=1.0,
                    completed=True,
                )
                return SimpleNamespace(
                    request=request, intent=AgentIntent.CREATE_QUOTE,
                    plan=plan, requires_manual_review=False,
                )
        elif "Nowa oferta" in labels:
            action = AgentAction(
                name="click_screen_element",
                description="Open the new offer dialog.",
                target="Nowa oferta",
            )
        elif "Szerokość" in labels and labels["Szerokość"].metadata.get("current_value", "") == "":
            action = AgentAction(
                name="write_text",
                description="Enter the requested width.",
                target="Szerokość",
                value="9999" if self.wrong_width else "1200",
            )
        elif "Wysokość" in labels and labels["Wysokość"].metadata.get("current_value", "") == "":
            action = AgentAction(
                name="write_text",
                description="Enter the requested height.",
                target="Wysokość",
                value="1500",
            )
        elif "Zapisz szkic" in labels and "Szkic zapisany" not in labels:
            action = AgentAction(
                name="click_screen_element",
                description="Save the offer as a draft.",
                target="Zapisz szkic",
            )
        elif "Szkic zapisany" in labels:
            plan = ActionPlan(
                intent=AgentIntent.CREATE_QUOTE,
                steps=(),
                confidence=1.0,
                completed=True,
            )
            return SimpleNamespace(
                request=request, intent=AgentIntent.CREATE_QUOTE,
                plan=plan, requires_manual_review=False,
            )

        if action is None:
            return SimpleNamespace(
                request=request, intent=AgentIntent.CREATE_QUOTE,
                plan=None, requires_manual_review=True,
                get_value=lambda _key: "no_supported_next_action",
            )

        plan = ActionPlan(
            intent=AgentIntent.CREATE_QUOTE,
            steps=(ActionStep(index=1, action=action),),
            confidence=1.0,
        )
        return SimpleNamespace(
            request=request, intent=AgentIntent.CREATE_QUOTE,
            plan=plan, requires_manual_review=False,
        )


def make_host(tmp_path, *, orchestrator=None, control=None, final_verifier=None):
    control = control or SimulatedWindowHubControlLoop()
    host = WindowHubResumableTaskHost(
        control_loop=control,
        orchestrator=orchestrator or SimulatedOfferOrchestrator(),
        repository=TaskCheckpointRepository(tmp_path),
        final_verifier=final_verifier,
    )
    return host, control


def test_persisted_runner_completes_multistep_windowhub_draft_through_existing_control_loop(tmp_path):
    orchestrator = SimulatedOfferOrchestrator()
    host, control = make_host(tmp_path, orchestrator=orchestrator)
    initial = TaskCheckpoint(
        task_id="windowhub-draft-1",
        goal="Create a WindowHub draft offer for a window 1200 x 1500",
        facts={"width": 1200, "height": 1500},
        required_fields=("width", "height"),
        citations=({"source": "salesperson_request", "excerpt": "1200 x 1500"},),
        max_actions=6,
        max_reasoning_calls=8,
    )
    host.service.create(initial)

    for _ in range(8):
        # Each advance reloads the JSON checkpoint from disk.
        current = host.service.advance(initial.task_id)
        if current.status in {TaskStatus.COMPLETED, TaskStatus.STOPPED, TaskStatus.WAITING_FOR_INPUT,
                              TaskStatus.WAITING_FOR_CONFIRMATION}:
            break

    assert current.status == TaskStatus.COMPLETED
    assert control.executed_targets == ["Nowa oferta", "Szerokość", "Wysokość", "Zapisz szkic"]
    assert len(current.completed_steps) == 4
    assert [s.executed for s in current.steps] == [True, True, True, True]
    assert [s.verified for s in current.completed_steps] == [True, True, True, True]
    assert {e["field"] for e in current.final_evidence} == {"width", "height"}
    reloaded = host.service.get(initial.task_id)
    assert reloaded == current
    assert reloaded.draft_only is True
    assert orchestrator.application_knowledge["application"] == "WindowHub"


def test_conflicting_model_proposed_dimension_stops_before_control_loop_execution(tmp_path):
    host, control = make_host(tmp_path, orchestrator=SimulatedOfferOrchestrator(wrong_width=True))
    checkpoint = TaskCheckpoint(
        "windowhub-wrong-width",
        "Create a WindowHub draft offer 1200 x 1500",
        facts={"width": 1200, "height": 1500},
        required_fields=("width", "height"),
    )
    host.service.create(checkpoint)

    state = host.service.advance(checkpoint.task_id)
    assert state.status == TaskStatus.READY
    state = host.service.advance(checkpoint.task_id)
    assert state.status == TaskStatus.WAITING_FOR_INPUT
    assert control.executed_targets == ["Nowa oferta"]
    assert any("conflicts with the task's supplied fact" in issue for issue in state.unresolved_issues)


def test_runner_never_executes_owned_modal_field_scoped_to_another_document(tmp_path):
    control = SimulatedWindowHubControlLoop()
    control.scene = FakeScene(
        [
            FakeElement(
                "edit",
                "Szerokość",
                "writable",
                metadata={
                    "current_value": "",
                    "document_scope": "Inna oferta",
                    "uia_owned_modal": True,
                },
            ),
        ],
        active_document="Oferta robocza",
    )
    host, _ = make_host(tmp_path, control=control)
    checkpoint = TaskCheckpoint(
        "windowhub-cross-document-modal",
        "Enter width in the active WindowHub offer",
        facts={"width": 1200},
        required_fields=("width",),
        max_actions=2,
        max_reasoning_calls=2,
    )
    host.service.create(checkpoint)

    after = host.service.advance(checkpoint.task_id)

    assert control.executed_targets == []
    assert after.status is not TaskStatus.COMPLETED
    assert any("different document" in issue for issue in after.unresolved_issues)


def test_submission_target_is_stopped_at_confirmation_checkpoint_until_explicit_approval(tmp_path):
    control = SimulatedWindowHubControlLoop()
    control.scene = FakeScene([FakeElement("button", "Wyślij ofertę")], active_document="Oferta robocza")
    host, _ = make_host(tmp_path, orchestrator=SimulatedOfferOrchestrator(submit=True), control=control)
    checkpoint = TaskCheckpoint(
        "windowhub-submit-1",
        "Submit offer only after approval",
        max_actions=3,
        max_reasoning_calls=3,
    )
    host.service.create(checkpoint)

    waiting = host.service.advance(checkpoint.task_id)
    assert waiting.status == TaskStatus.WAITING_FOR_CONFIRMATION
    assert control.executed_targets == []

    host.service.approve_pending_action(checkpoint.task_id, approve_submission=True)
    after = host.service.advance(checkpoint.task_id)
    assert control.executed_targets == ["Wyślij ofertę"]
    assert after.steps[-1].executed is True
    assert after.draft_only is False


def test_final_fields_must_match_current_document_values(tmp_path):
    control = SimulatedWindowHubControlLoop()
    control.scene = FakeScene(
        [
            FakeElement("edit", "Szerokość", "writable", metadata={"current_value": "1200", "document_scope": "Oferta robocza"}),
            FakeElement("edit", "Wysokość", "writable", metadata={"current_value": "999", "document_scope": "Oferta robocza"}),
            FakeElement("text", "Szkic zapisany", metadata={"document_scope": "Oferta robocza"}),
        ],
        active_document="Oferta robocza",
    )
    host, _ = make_host(
        tmp_path,
        control=control,
        orchestrator=SimulatedOfferOrchestrator(),
    )
    checkpoint = TaskCheckpoint(
        "windowhub-mismatch-final",
        "Create draft offer 1200 x 1500",
        facts={"width": 1200, "height": 1500},
        required_fields=("width", "height"),
    )
    host.service.create(checkpoint)
    state = host.service.advance(checkpoint.task_id)
    assert state.status == TaskStatus.STOPPED
    assert "height" in state.unresolved_issues[-1]

def test_final_verification_fails_closed_when_active_document_is_unresolved():
    # A matching value may still belong to a different document. The final
    # verifier must never fall back to reading every visible Edit/ComboBox.
    scene = FakeScene(
        [
            FakeElement(
                "edit",
                "Szerokość",
                "writable",
                metadata={
                    "current_value": "1200",
                    "document_scope": "OFR/4295-",
                },
            ),
            FakeElement(
                "edit",
                "Wysokość",
                "writable",
                metadata={
                    "current_value": "1500",
                    "document_scope": "OFR/4295-",
                },
            ),
        ],
        active_document=None,
    )
    checkpoint = TaskCheckpoint(
        "windowhub-unresolved-document",
        "Verify width and height in the active offer",
        facts={"width": 1200, "height": 1500},
        required_fields=("width", "height"),
    )

    result = verify_windowhub_final_state(checkpoint, scene)

    assert result.verified is False
    assert set(result.missing_fields) == {"width", "height"}
    assert "active document is unresolved" in result.reason.casefold()
    assert result.evidence[0]["reason"] == "active_document_unresolved"

def test_final_verification_ignores_matching_fields_with_unknown_document_scope():
    # This models the real-app diagnostic: an active document tab can be
    # resolved while generic UIA fields still have unknown document scope.
    scene = FakeScene(
        [
            FakeElement(
                "edit",
                "Szerokość",
                "writable",
                metadata={"current_value": "1200"},
            ),
            FakeElement(
                "edit",
                "Wysokość",
                "writable",
                metadata={"current_value": "1500"},
            ),
        ],
        active_document="OFR/4300-",
    )
    checkpoint = TaskCheckpoint(
        "windowhub-unknown-field-scope",
        "Verify width and height are attached to the selected offer",
        facts={"width": 1200, "height": 1500},
        required_fields=("width", "height"),
    )

    result = verify_windowhub_final_state(checkpoint, scene)

    assert result.verified is False
    assert set(result.missing_fields) == {"width", "height"}
    assert "missing or ambiguous fields" in result.reason



def _make_write_validation_scene(*, active_document="Oferta robocza", target_scope="Oferta robocza",
                                 metadata=None, kind="edit", capability="writable"):
    element_metadata = dict(metadata or {})
    if target_scope is not None:
        element_metadata["document_scope"] = target_scope
    return FakeScene(
        [FakeElement(kind, "Szerokość", capability, metadata=element_metadata)],
        active_document=active_document,
    )


def _validate_write_target(scene):
    return WindowHubResumableTaskHost._validate_target(
        TaskAction(
            action_id="scope-check",
            name="write_text",
            target="Szerokość",
            scene_fingerprint="synthetic-scene",
            value="1200",
        ),
        scene,
    )


def test_write_text_accepts_edit_field_scoped_to_active_document():
    scene = _make_write_validation_scene(
        metadata={"current_value": "", "source": "windowhub_ui_automation"},
    )

    result = _validate_write_target(scene)

    assert result.valid is True
    assert result.target == "Szerokość"


def test_write_text_rejects_unique_unscoped_edit_with_active_document():
    scene = _make_write_validation_scene(target_scope=None)

    result = _validate_write_target(scene)

    assert result.valid is False
    assert "scope evidence" in result.reason


def test_write_text_rejects_field_scoped_to_another_document():
    scene = _make_write_validation_scene(target_scope="Inna oferta")

    result = _validate_write_target(scene)

    assert result.valid is False
    assert (
        "scope evidence" in result.reason
        or "outside active document" in result.reason
    )


def test_write_text_rejects_owned_modal_with_conflicting_document_scope():
    scene = _make_write_validation_scene(
        target_scope="Inna oferta",
        metadata={"uia_owned_modal": True, "current_value": ""},
    )

    result = _validate_write_target(scene)

    assert result.valid is False
    assert "different document" in result.reason


def test_write_text_accepts_supported_edit_field_in_explicit_owned_modal():
    scene = _make_write_validation_scene(
        target_scope=None,
        metadata={"uia_owned_modal": True, "current_value": ""},
    )

    result = _validate_write_target(scene)

    assert result.valid is True


def test_write_text_rejects_unscoped_edit_when_active_document_is_unresolved():
    scene = _make_write_validation_scene(active_document=None, target_scope="Oferta robocza")

    result = _validate_write_target(scene)

    assert result.valid is False
    assert "requires a resolved active document" in result.reason


def test_write_text_rejects_non_editable_target_even_when_document_scoped():
    scene = _make_write_validation_scene(
        metadata={},
        kind="button",
        capability="clickable",
    )

    result = _validate_write_target(scene)

    assert result.valid is False
    assert "not an evidenced editable text field" in result.reason



def test_final_verification_accepts_product_type_only_from_selected_active_document_item():
    scene = FakeScene(
        [
            FakeElement(
                "list_item",
                "Okno",
                metadata={
                    "uia_selected": True,
                    "document_scope": "Oferta robocza",
                },
            ),
            FakeElement(
                "edit",
                "Szerokość",
                "writable",
                metadata={
                    "current_value": "1200",
                    "document_scope": "Oferta robocza",
                },
            ),
            FakeElement(
                "edit",
                "Wysokość",
                "writable",
                metadata={
                    "current_value": "1500",
                    "document_scope": "Oferta robocza",
                },
            ),
        ],
        active_document="Oferta robocza",
    )
    checkpoint = TaskCheckpoint(
        "product-type-selected",
        "Verify selected product and dimensions",
        facts={"product_type": "window", "width": 1200, "height": 1500},
        required_fields=("product_type", "width", "height"),
    )

    result = verify_windowhub_final_state(checkpoint, scene)

    assert result.verified is True
    product = next(item for item in result.evidence if item["field"] == "product_type")
    assert product["verification"] == "selected_product_item"
    assert product["observed_value"] == "window"


def test_final_verification_rejects_unselected_product_item():
    scene = FakeScene(
        [
            FakeElement(
                "list_item",
                "Okno",
                metadata={"uia_selected": False, "document_scope": "Oferta robocza"},
            ),
            FakeElement(
                "edit",
                "Szerokość",
                "writable",
                metadata={"current_value": "1200", "document_scope": "Oferta robocza"},
            ),
            FakeElement(
                "edit",
                "Wysokość",
                "writable",
                metadata={"current_value": "1500", "document_scope": "Oferta robocza"},
            ),
        ],
        active_document="Oferta robocza",
    )
    checkpoint = TaskCheckpoint(
        "product-type-not-selected",
        "Verify selected product and dimensions",
        facts={"product_type": "window", "width": 1200, "height": 1500},
        required_fields=("product_type", "width", "height"),
    )

    result = verify_windowhub_final_state(checkpoint, scene)

    assert result.verified is False
    assert "product_type" in result.missing_fields
    assert "selected_product_missing_or_ambiguous" in str(result.evidence)


def test_final_verification_rejects_wrong_selected_product_type():
    scene = FakeScene(
        [
            FakeElement(
                "list_item",
                "Drzwi",
                metadata={"uia_selected": True, "document_scope": "Oferta robocza"},
            ),
            FakeElement(
                "edit",
                "Szerokość",
                "writable",
                metadata={"current_value": "1200", "document_scope": "Oferta robocza"},
            ),
            FakeElement(
                "edit",
                "Wysokość",
                "writable",
                metadata={"current_value": "1500", "document_scope": "Oferta robocza"},
            ),
        ],
        active_document="Oferta robocza",
    )
    checkpoint = TaskCheckpoint(
        "wrong-product-selected",
        "Verify selected product and dimensions",
        facts={"product_type": "window", "width": 1200, "height": 1500},
        required_fields=("product_type", "width", "height"),
    )

    result = verify_windowhub_final_state(checkpoint, scene)

    assert result.verified is False
    assert "product_type" in result.missing_fields
    product = next(item for item in result.evidence if item["field"] == "product_type")
    assert product["observed_value"] == "door"

class PdfQuoteDraftControlLoop(SimulatedWindowHubControlLoop):
    """Synthetic WindowHub surface with an explicitly selected window product."""

    def run(self, *, plan, context):
        action = plan.steps[0].action
        result = super().run(plan=plan, context=context)
        if (
            action.name == "click_screen_element"
            and action.target == "Nowa oferta"
            and result.success
        ):
            self.scene.elements = [
                FakeElement(
                    "list_item",
                    "Okno",
                    metadata={
                        "uia_selected": True,
                        "document_scope": "Oferta robocza",
                    },
                ),
                *self.scene.elements,
            ]
        return result


def test_pdf_to_windowhub_draft_e2e_requires_approval_then_verifies_saved_draft(tmp_path):
    from app.agent.adapters.pdf_document_adapter import PdfDocumentAdapter
    from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
    from app.agent.runtime.agent_runtime import AgentRuntime
    from app.agent.session.agent_session_store import AgentSessionStore
    from tests.test_pdf_document_adapter import write_text_pdf

    root = tmp_path / "approved"
    root.mkdir()
    source = root / "offer.pdf"
    write_text_pdf(
        source,
        [
            "Product: window",
            "Width: 1200 mm",
            "Height: 1500 mm",
        ],
    )

    control = PdfQuoteDraftControlLoop()
    orchestrator = SimulatedOfferOrchestrator()
    runtime = AgentRuntime(
        orchestrator=orchestrator,
        plan_executor=object(),
        session_store=AgentSessionStore(),
        control_loop=control,
        pdf_ingestion_service=PdfIngestionService(
            adapter=PdfDocumentAdapter(allowed_roots=(root,)),
        ),
    )
    runtime.configure_windowhub_resumable_tasks(
        repository=TaskCheckpointRepository(tmp_path / "checkpoints"),
    )
    runtime.ingest_pdf(source, source_alias="e2e-offer")

    task_id = "pdf-to-windowhub-draft-e2e"
    started = runtime.start_pdf_quote_task(
        "e2e-offer",
        request_message="Prepare a draft WindowHub offer from the supplied PDF.",
        task_id=task_id,
    )

    assert started.task_created is True
    assert started.requires_manual_review is False
    pending = started.checkpoint
    assert pending is not None
    assert pending.status is TaskStatus.WAITING_FOR_APPROVAL
    assert pending.approval_required is True
    assert pending.execution_approved is False
    assert pending.draft_only is True
    assert pending.facts["product_type"] == "window"
    assert pending.facts["width"] == 1200
    assert pending.facts["height"] == 1500
    assert control.observe_calls == 0
    assert control.executed_targets == []

    approved = runtime.approve_resumable_task_execution(task_id)
    assert approved.status is TaskStatus.READY
    assert approved.execution_approved is True

    current = approved
    for _ in range(8):
        current = runtime.advance_resumable_task(task_id)
        if current.status in {
            TaskStatus.COMPLETED,
            TaskStatus.STOPPED,
            TaskStatus.WAITING_FOR_INPUT,
            TaskStatus.WAITING_FOR_CONFIRMATION,
        }:
            break

    assert current.status is TaskStatus.COMPLETED
    assert control.executed_targets == [
        "Nowa oferta",
        "Szerokość",
        "Wysokość",
        "Zapisz szkic",
    ]
    assert control.observe_calls > len(control.executed_targets)
    assert len(current.completed_steps) == 4
    assert all(step.executed and step.execution_success and step.verified for step in current.completed_steps)
    assert current.draft_only is True
    assert current.stop_reason is None
    assert {
        item["field"]
        for item in current.final_evidence
    } == {"product_type", "width", "height"}
    assert current.final_evidence
    assert runtime.get_resumable_task(task_id) == current
    assert orchestrator.application_knowledge["application"] == "WindowHub"



def test_new_offer_cross_document_click_routes_to_unique_unselected_start1():
    control = SimulatedWindowHubControlLoop()
    control.scene = FakeScene(
        [
            FakeElement(
                "button",
                "Nowa oferta",
                metadata={
                    "document_scope": "Start1",
                    "uia_visible": True,
                    "uia_enabled": True,
                },
            ),
            FakeElement(
                "tabitem",
                "Start1",
                metadata={
                    "uia_tab_scope": "document",
                    "uia_document_tab_selected": False,
                    "uia_visible": True,
                    "uia_enabled": True,
                },
            ),
            FakeElement(
                "tabitem",
                "OFR/3419",
                metadata={
                    "uia_tab_scope": "document",
                    "uia_document_tab_selected": True,
                },
            ),
        ],
        active_document="OFR/3419",
    )
    host = WindowHubResumableTaskHost(
        control_loop=control,
        orchestrator=SimulatedOfferOrchestrator(),
    )
    checkpoint = TaskCheckpoint(
        "start1-cross-document-route",
        "Prepare a new WindowHub offer",
    )

    decision = host._plan_next(checkpoint, control.scene)

    assert decision.action is not None
    assert decision.action.name == "click_screen_element"
    assert decision.action.target == "Start1"
    assert "Re-observe" in decision.action.expected_state["description"]
    assert control.executed_targets == []

    validation = host._validate_target(decision.action, control.scene)
    assert validation.valid is True


def test_click_target_with_conflicting_document_scope_is_rejected():
    scene = FakeScene(
        [
            FakeElement(
                "button",
                "Nowa oferta",
                metadata={
                    # Deliberately make the normal resolver's tracked-ID path
                    # return this control so the host-level scope guard is tested.
                    "tracked_object_id": "Nowa oferta",
                    "document_scope": "Start1",
                },
            )
        ],
        active_document="OFR/3419",
    )
    action = TaskAction(
        action_id="cross-document-click",
        name="click_screen_element",
        target="Nowa oferta",
        scene_fingerprint="test-scene",
    )

    validation = WindowHubResumableTaskHost._validate_target(action, scene)

    assert validation.valid is False
    assert validation.reason == "click target is scoped to a different document"
