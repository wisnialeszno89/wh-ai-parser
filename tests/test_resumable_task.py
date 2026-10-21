from dataclasses import dataclass, field

import pytest

from app.agent.runtime.resumable_task import (
    Execution, PlanDecision, ResumableTaskRunner, TaskAction, TaskCheckpoint,
    TaskStatus, Validation, Verification, fingerprint_scene,
)


@dataclass
class Element:
    kind: str
    label: str
    interaction_capability: str = "clickable"
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class State:
    active_application: str = "WindowHub"
    active_window_title: str = "WindowHub"


@dataclass
class Observation:
    state: State = field(default_factory=State)


@dataclass
class Scene:
    elements: list[Element]
    observation: Observation = field(default_factory=Observation)
    metadata: dict = field(default_factory=dict)


class Harness:
    def __init__(self, scene): self.scene, self.observe_count = scene, 0
    def observe(self): self.observe_count += 1; return self.scene


def validator(action, scene):
    matches = [e for e in scene.elements if e.label.casefold() == action.target.casefold()]
    if len(matches) != 1: return Validation(False, reason="semantic target is missing or ambiguous")
    return Validation(True, matches[0].label, "unique current-scene target", matches[0])


def make_runner(harness, *, planner, executor, action_verifier=None, final_verifier=None):
    return ResumableTaskRunner(
        observe=harness.observe, plan_next=planner, validate_action=validator, execute_action=executor,
        verify_action=action_verifier or (lambda action, result, scene: Verification(
            result.success and result.executed, evidence=({"post_scene": [e.label for e in scene.elements]},),
            reason="execution and observed state confirmed")),
        verify_final_state=final_verifier or (lambda state, scene: Verification(
            True, evidence=({"fields_verified": sorted(state.facts)},))),
    )


def action(action_id, target, scene, **kwargs):
    return TaskAction(action_id, "click_screen_element" if kwargs.get("value") is None else "write_text",
                      target, fingerprint_scene(scene), **kwargs)


def test_resumable_multistep_draft_workflow_reobserves_and_verifies_final_state():
    scene = Scene([Element("button", "Nowa oferta")]); harness = Harness(scene); executed = []
    def planner(state, observed):
        vals = {e.label: e.metadata.get("current_value") for e in observed.elements}
        if "Nowa oferta" in vals: return PlanDecision(action=action("open-draft", "Nowa oferta", observed))
        if "Szerokość" in vals and vals["Szerokość"] != "1200": return PlanDecision(action=action("fill-width", "Szerokość", observed, value="1200"))
        if "Wysokość" in vals and vals["Wysokość"] != "1500": return PlanDecision(action=action("fill-height", "Wysokość", observed, value="1500"))
        return PlanDecision(complete=True)
    def executor(a, observed, resolved):
        executed.append((a.action_id, resolved.target))
        if a.action_id == "open-draft": scene.elements = [Element("textbox", "Szerokość", "writable", metadata={"current_value": ""})]
        elif a.action_id == "fill-width": scene.elements = [Element("textbox", "Szerokość", "writable", metadata={"current_value": "1200"}), Element("textbox", "Wysokość", "writable", metadata={"current_value": ""})]
        elif a.action_id == "fill-height": scene.elements = [Element("textbox", "Szerokość", "writable", metadata={"current_value": "1200"}), Element("textbox", "Wysokość", "writable", metadata={"current_value": "1500"})]
        return Execution(True, True, "executed", resolved.target, "fake.semantic_executor")
    def verify_final(state, observed):
        values = {e.label: e.metadata.get("current_value") for e in observed.elements}
        ok = values.get("Szerokość") == "1200" and values.get("Wysokość") == "1500"
        return Verification(ok, evidence=({"width": values.get("Szerokość"), "height": values.get("Wysokość")},),
                            missing_fields=() if ok else ("width", "height"), reason="final fields independently verified")
    runner = make_runner(harness, planner=planner, executor=executor, final_verifier=verify_final)
    state = TaskCheckpoint("draft-1", "Create draft quotation", facts={"width": 1200, "height": 1500},
                           required_fields=("width", "height"), citations=({"source": "user_request", "excerpt": "1200 x 1500"},),
                           max_actions=4, max_reasoning_calls=5)
    for _ in range(5):
        state = TaskCheckpoint.from_payload(state.to_payload())
        state = runner.advance(state)
        state = TaskCheckpoint.from_payload(state.to_payload())
        if state.status == TaskStatus.COMPLETED: break
    assert state.status == TaskStatus.COMPLETED
    assert [x[0] for x in executed] == ["open-draft", "fill-width", "fill-height"]
    assert len(state.completed_steps) == 3
    assert all(x.executor_path == "fake.semantic_executor" for x in state.completed_steps)
    assert state.final_evidence[0]["width"] == "1200"
    assert harness.observe_count >= 6 and state.draft_only


def test_missing_fields_block_planning_until_user_supplies_values():
    scene = Scene([Element("button", "Nowa oferta")]); harness = Harness(scene); plans=[]; runs=[]
    runner = make_runner(harness, planner=lambda s,o: plans.append(1) or PlanDecision(action=action("a", "Nowa oferta", o)),
                         executor=lambda *args: runs.append(1) or Execution(True, True, "ok"))
    waiting = runner.advance(TaskCheckpoint("t", "Draft", required_fields=("width", "height")))
    assert waiting.status == TaskStatus.WAITING_FOR_INPUT and waiting.missing_fields == ("width", "height")
    assert not plans and not runs
    ready = waiting.with_facts({"width": 1200, "height": 1500})
    assert ready.status == TaskStatus.READY and not ready.unresolved_issues
    assert runner.advance(ready).status == TaskStatus.READY and len(runs) == 1


def test_ambiguous_target_is_rejected_before_executor():
    scene = Scene([Element("button", "OK"), Element("button", "OK")]); h=Harness(scene); runs=[]
    runner=make_runner(h, planner=lambda s,o: PlanDecision(action=action("ok", "OK", o)),
                       executor=lambda *args: runs.append(1) or Execution(True, True, "unsafe"))
    result=runner.advance(TaskCheckpoint("t", "Confirm"))
    assert result.status == TaskStatus.STOPPED and not result.steps[-1].executed
    assert "ambiguous" in result.steps[-1].reason and not runs


def test_stale_scene_action_is_rejected_before_executor():
    scene=Scene([Element("button", "Nowa oferta")]); h=Harness(scene); runs=[]
    runner=make_runner(h, planner=lambda s,o: PlanDecision(action=TaskAction("stale", "click_screen_element", "Nowa oferta", "old")),
                       executor=lambda *args: runs.append(1) or Execution(True, True, "unsafe"))
    result=runner.advance(TaskCheckpoint("t", "Start"))
    assert result.status == TaskStatus.STOPPED and result.stop_reason == "stale_scene_action_rejected_before_execution"
    assert not result.steps[-1].executed and not runs


def test_failed_action_requires_explicit_review_before_replanning():
    scene=Scene([Element("button", "Nowa oferta")]); h=Harness(scene); calls=[]
    def planner(s,o): return PlanDecision(action=action(f"a{len(calls)+1}", "Nowa oferta", o))
    def executor(a,o,v):
        calls.append(a.action_id)
        return Execution(len(calls)>1, True, "failed" if len(calls)==1 else "ok", v.target, "fake")
    runner=make_runner(h, planner=planner, executor=executor)
    stopped=runner.advance(TaskCheckpoint("t", "Start")); assert stopped.status == TaskStatus.STOPPED and calls == ["a1"]
    resumed=stopped.resume_after_review()
    for issue in tuple(resumed.unresolved_issues): resumed=resumed.resolve_issue(issue)
    next_state=runner.advance(resumed)
    assert calls == ["a1", "a2"] and len(next_state.completed_steps)==1
    assert not next_state.steps[0].verified and next_state.steps[1].action_id=="a2"


def test_submission_requires_action_bound_explicit_approval():
    scene=Scene([Element("button", "Wyślij ofertę")]); h=Harness(scene); runs=[]
    runner=make_runner(h, planner=lambda s,o: PlanDecision(action=TaskAction("send1", "click_screen_element", "Wyślij ofertę", fingerprint_scene(o), submission=True)),
                       executor=lambda a,o,v: runs.append(a.action_id) or Execution(True, True, "sent", v.target, "fake"))
    waiting=runner.advance(TaskCheckpoint("t", "Create draft"))
    assert waiting.status == TaskStatus.WAITING_FOR_CONFIRMATION and not runs
    with pytest.raises(ValueError, match="explicit"): waiting.approve_pending_action()
    approved=waiting.approve_pending_action(approve_submission=True)
    assert not approved.draft_only
    assert runner.advance(approved).status == TaskStatus.READY and runs == ["send1"]


def test_successful_click_does_not_replace_final_field_verification():
    scene=Scene([Element("button", "Zapisz szkic")]); h=Harness(scene)
    def planner(s,o): return PlanDecision(action=action("save", "Zapisz szkic", o)) if any(e.label=="Zapisz szkic" for e in o.elements) else PlanDecision(complete=True)
    def executor(a,o,v): scene.elements=[Element("text", "Szkic zapisany")]; return Execution(True, True, "click ok", v.target, "fake")
    runner=make_runner(h, planner=planner, executor=executor, final_verifier=lambda s,o: Verification(False, evidence=({"width":"1200"},), missing_fields=("height",), reason="height not visible"))
    after=runner.advance(TaskCheckpoint("t", "Draft", facts={"width":1200, "height":1500}))
    assert after.status == TaskStatus.READY and after.completed_steps[0].verified
    result=runner.advance(after)
    assert result.status == TaskStatus.STOPPED and result.stop_reason == "height not visible"
    assert any("Final state not verified: height" == x for x in result.unresolved_issues)


def test_reasoning_budget_and_citations_survive_json_roundtrip():
    scene=Scene([Element("button", "Nowa oferta")]); h=Harness(scene)
    runner=make_runner(h, planner=lambda s,o: PlanDecision(), executor=lambda *args: Execution(True, True, "unused"))
    state=TaskCheckpoint("t", "goal", citations=({"source_id":"pdf-1", "page":2},), max_actions=2, max_reasoning_calls=1)
    stopped=runner.advance(state)
    assert stopped.status == TaskStatus.STOPPED and stopped.reasoning_calls == 1
    resumed=stopped.resume_after_review()
    for issue in tuple(resumed.unresolved_issues): resumed=resumed.resolve_issue(issue)
    capped=runner.advance(resumed)
    assert capped.status == TaskStatus.STOPPED and capped.stop_reason == "reasoning_budget_exhausted"
    assert TaskCheckpoint.from_payload(state.to_payload()).citations == ({"source_id":"pdf-1", "page":2},)


def test_approved_action_is_not_replayed_when_scene_changes_before_execution():
    scene = Scene([Element("button", "Zapisz szkic")]); harness = Harness(scene); runs=[]
    runner = make_runner(
        harness,
        planner=lambda s,o: PlanDecision(action=TaskAction(
            "save-confirmed", "click_screen_element", "Zapisz szkic", fingerprint_scene(o), requires_confirmation=True)),
        executor=lambda a,o,v: runs.append(a.action_id) or Execution(True, True, "ok", v.target, "fake"),
    )
    waiting = runner.advance(TaskCheckpoint("t", "Save draft"))
    assert waiting.status == TaskStatus.WAITING_FOR_CONFIRMATION
    approved = waiting.approve_pending_action()
    scene.elements = [Element("button", "Anuluj")]
    result = runner.advance(approved)
    assert result.status == TaskStatus.STOPPED
    assert result.stop_reason == "stale_scene_before_approved_action"
    assert runs == []

def test_final_missing_fields_block_completion_even_if_verifier_claims_success():
    scene = Scene([Element("text", "Szkic zapisany")]); harness = Harness(scene)
    runner = make_runner(
        harness, planner=lambda s,o: PlanDecision(complete=True),
        executor=lambda *args: Execution(True, True, "unused"),
        final_verifier=lambda s,o: Verification(True, evidence=({"width": "1200"},),
                                                  missing_fields=("height",), reason=""),
    )
    result = runner.advance(TaskCheckpoint("t", "Verify draft", facts={"width":1200, "height":1500}))
    assert result.status == TaskStatus.STOPPED
    assert result.stop_reason == "final_state_verification_failed"
    assert "Final state not verified: height" in result.unresolved_issues

@pytest.mark.parametrize(
    "target",
    (
        "Wyślij ofertę",
        "Zatwierdź ofertę",
        "Finalizuj ofertę",
        "Przekaż do realizacji",
        "Confirm order",
        "Approve quotation",
        "Dispatch order",
    ),
)
def test_submission_like_targets_require_action_bound_confirmation(target):
    action = TaskAction(
        action_id="submit-gate",
        name="click_screen_element",
        target=target,
        scene_fingerprint="scene-current",
    )

    assert action.is_submission is True
    assert action.confirmation_required is True

