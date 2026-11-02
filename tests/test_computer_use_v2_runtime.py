from types import SimpleNamespace

from app.agent.agent_intent import AgentIntent
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)
from app.agent.runtime.windows_desktop_v2_agent_runtime import (
    WindowsDesktopV2AgentRuntime,
)
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.outcome_verifier import OutcomeVerifier
from app.agent.verification.verification_result import VerificationResult


def _scene():
    evidence = SemanticEvidence(
        source=EvidenceSource.ACCESSIBILITY,
        kind=EvidenceKind.LABEL,
        value="Save",
        confidence=0.99,
        element_id="uia:save",
    )
    element = ScreenElement(
        kind="button",
        label="Save",
        x=10,
        y=20,
        width=100,
        height=30,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        evidence=(evidence,),
        metadata={
            "source": "windows_ui_automation",
            "uia_control_type": "button",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_selected": False,
            "uia_runtime_id": "[1,2,3]",
            "interaction_capability_confidence": 0.99,
        },
    )
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="EXCEL.EXE",
                active_window_title="Workbook - Excel",
            ),
            metadata={
                "window_handle": 501,
                "window_rect": SimpleNamespace(left=0, top=0),
            },
        ),
        elements=(element,),
    )


class _Reasoner:
    def __init__(self, decision_factory):
        self.decision_factory = decision_factory
        self.calls = 0
        self.last_error = None

    def reason(self, request):
        self.calls += 1
        return self.decision_factory(request, self.calls)


class _ControlLoop:
    def __init__(self, scene, *, executed, verified):
        self.scene = scene
        self.executed = executed
        self.verified = verified
        self.observe_calls = 0
        self.run_calls = 0
        self.last_plan = None
        self.last_context = None

    def observe_scene(self):
        self.observe_calls += 1
        return self.scene

    def run(self, *, plan, context):
        self.run_calls += 1
        self.last_plan = plan
        self.last_context = context
        execution = SimpleNamespace(
            success=True,
            message="fake execution",
            metadata={"executed": self.executed},
        )
        verification = (
            VerificationResult(
                verified=True,
                reason="verified",
                confidence=1.0,
            )
            if self.verified
            else None
        )
        attempt = SimpleNamespace(
            execution_result=execution,
            verification_result=verification,
        )
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            last_execution_result=SimpleNamespace(last_attempt=attempt),
        )


def _act_response(request, *, postcondition):
    capability = request["capabilities"]["actions"][0]
    return {
        "version": "2",
        "task_id": request["task_id"],
        "decision": "act",
        "rationale": "Save the current workbook.",
        "confidence": 0.97,
        "observation_request": None,
        "action": {
            "name": capability["name"],
            "target_ref": capability["target_ref"],
            "value": None,
            "expected_postcondition": postcondition,
            "requires_confirmation": capability["requires_confirmation"],
        },
        "completion": None,
        "requires_manual_review": False,
    }


def _done_response(request):
    evidence_ref = request["world"]["evidence"][0]["ref"]
    return {
        "version": "2",
        "task_id": request["task_id"],
        "decision": "done",
        "rationale": "The task is complete.",
        "confidence": 0.99,
        "observation_request": None,
        "action": None,
        "completion": {"evidence_refs": [evidence_ref]},
        "requires_manual_review": False,
    }


def test_v2_runtime_does_not_treat_dry_run_as_successful_computer_action():
    scene = _scene()
    reasoner = _Reasoner(
        lambda request, _call: _act_response(
            request,
            postcondition={"kind": "scene_changed"},
        )
    )
    control = _ControlLoop(scene, executed=False, verified=False)

    result = WindowsDesktopV2AgentRuntime(
        control_loop=control,
        reasoner=reasoner,
    ).run("Save the workbook", max_cycles=2)

    assert result.success is False
    assert result.completed is False
    assert result.stopped is True
    assert result.reason == "dry_run_no_hardware_action_performed"
    assert result.cycles[0].executed is False
    assert control.run_calls == 1


def test_v2_runtime_reasons_again_only_after_verified_live_action():
    scene = _scene()
    reasoner = _Reasoner(
        lambda request, call: (
            _act_response(
                request,
                postcondition={"kind": "scene_changed"},
            )
            if call == 1
            else _done_response(request)
        )
    )
    control = _ControlLoop(scene, executed=True, verified=True)

    result = WindowsDesktopV2AgentRuntime(
        control_loop=control,
        reasoner=reasoner,
    ).run("Save the workbook", max_cycles=3)

    assert result.success is True
    assert result.completed is True
    assert result.stopped is False
    assert len(result.cycles) == 2
    assert result.cycles[0].executed is True
    assert result.cycles[0].verified is True
    assert result.cycles[1].decision == "done"
    assert control.run_calls == 1
    assert control.observe_calls == 2
    assert control.last_plan.intent is AgentIntent.COMPUTER_USE
    assert control.last_plan.steps[0].action.name == "click_screen_element"


def test_v2_runtime_maps_element_state_postcondition_to_local_verification():
    scene = _scene()
    reasoner = _Reasoner(
        lambda request, _call: _act_response(
            request,
            postcondition={
                "kind": "entity_state_equals",
                "target_ref": "ent_0001",
                "state": "uia_selected",
                "expected_value": False,
            },
        )
    )
    control = _ControlLoop(scene, executed=True, verified=True)

    result = WindowsDesktopV2AgentRuntime(
        control_loop=control,
        reasoner=reasoner,
    ).run("Save the workbook", max_cycles=1)

    expected = control.last_context.get_value("expected_outcomes")[
        "click_screen_element"
    ]
    assert isinstance(expected, ExpectedOutcome)
    assert expected.expected_element_state_name == "uia_selected"
    assert expected.expected_element_state_value is False
    assert result.cycles[0].verified is True


def test_outcome_verifier_checks_a_named_ui_automation_state():
    scene = _scene()
    expected = ExpectedOutcome(
        description="The control should be selected.",
        expected_element_label="Save",
        expected_element_state_name="uia_selected",
        expected_element_state_value=True,
    )

    result = OutcomeVerifier().verify(expected, scene)

    assert result.verified is False
    assert result.reason == "Targeted semantic element state did not match."
