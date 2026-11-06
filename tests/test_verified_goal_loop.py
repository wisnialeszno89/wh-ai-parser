from app.agent.runtime.verified_goal_loop import GoalDecision, GoalStep, run_verified_goal

def setup(*, approve=False, verified=True):
    state = {"width": ""}
    calls = {"execute": 0}
    def execute(step):
        calls["execute"] += 1
        state["width"] = step.value
        return True
    def run(decide, **kwargs):
        return run_verified_goal(
            observe=lambda: dict(state),
            decide=decide,
            execute=execute,
            verify_action=lambda step, before, after: verified and after["width"] == step.value,
            verify_goal=lambda obs: obs["width"] == "1500",
            fingerprint=lambda obs: obs["width"],
            approve_persistent=approve,
            **kwargs,
        )
    return run, calls

def test_success_is_verified_by_observation():
    run, calls = setup()
    result = run(lambda scene, trace: GoalDecision("act", GoalStep("write_text", "width", "equals_1500", "1500")))
    assert result.status == "verified"
    assert result.actions == 1
    assert result.observations == 2

def test_model_done_does_not_count_as_success():
    run, calls = setup()
    result = run(lambda scene, trace: GoalDecision("done"))
    assert result.status == "review"
    assert calls["execute"] == 0

def test_unverified_action_is_not_retried():
    run, calls = setup(verified=False)
    result = run(lambda scene, trace: GoalDecision("act", GoalStep("write_text", "width", "equals_1500", "1500")))
    assert result.status == "review"
    assert calls["execute"] == 1

def test_persistent_action_needs_approval():
    run, calls = setup()
    result = run(lambda scene, trace: GoalDecision("act", GoalStep("click", "save", "draft_saved", persistent=True)))
    assert result.reason == "persistent_action_needs_approval"
    assert calls["execute"] == 0

def test_hard_action_budget():
    state = {"n": 0}
    result = run_verified_goal(
        observe=lambda: dict(state),
        decide=lambda scene, trace: GoalDecision("act",GoalStep("click","next","scene_changed")),
        execute=lambda step: (state.update(n=state["n"]+1) or True),
        verify_action=lambda step, before, after: after["n"] > before["n"],
        verify_goal=lambda scene: False,
        fingerprint=lambda scene: str(scene["n"]),
        max_actions=2,
    )
    assert result.status == "budget_exhausted" and result.actions == 2

def test_repeat_without_progress_is_stopped():
    result = run_verified_goal(
        observe=lambda: {"same": True},
        decide=lambda scene, trace: GoalDecision("act",GoalStep("click","button","button_clicked")),
        execute=lambda step: True,
        verify_action=lambda step,before,after: True,
        verify_goal=lambda scene: False,
        fingerprint=lambda scene: "same",
    )
    assert result.reason == "repeated_action_without_progress" and result.actions == 1
