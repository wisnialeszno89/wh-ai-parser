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

    def observe_scene(self):
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
