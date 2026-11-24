"""V2 executor boundary tests: input arbiter is checked at loop.run()."""
from types import SimpleNamespace

import pytest

from app.agent.agent_action import AgentAction
from app.agent.runtime.navimind_local_input_arbiter import (
    InputDenied, LocalInputArbiter,
)
from app.agent.runtime.windowhub_goal_v2_coordinator import execute_v2_step


class FakeLoop:
    def __init__(self):
        self.calls = 0

    def run(self, *, plan, context):
        self.calls += 1
        assert len(plan.steps) == 1
        return SimpleNamespace(
            success=True,
            last_execution_result=SimpleNamespace(
                last_attempt=SimpleNamespace(
                    execution_result=SimpleNamespace(
                        success=True, metadata={"executed": True},
                    ),
                    verification_result=SimpleNamespace(verified=True),
                ),
            ),
        )


def patched_policy(monkeypatch):
    from app.agent.runtime import windowhub_goal_v2_coordinator as m
    monkeypatch.setattr(m, "enforce_v2_live_policy", lambda *a, **k: None)
    monkeypatch.setattr(
        m, "verified_v2_outcome",
        lambda *a, **k: SimpleNamespace(description="synthetic verified outcome"),
    )


def synthetic_scene():
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_application="Okna.exe",
                active_window_title="Wielkość okna",
            ),
            metadata={},
        ),
        metadata={},
    )


def resolved():
    return SimpleNamespace(
        action=AgentAction(
            name="write_text", description="synthetic draft edit",
            target="synthetic-control", value="123",
        )
    )


def test_v2_executor_dispatches_through_current_arbiter_permit(monkeypatch):
    patched_policy(monkeypatch)
    gate = LocalInputArbiter()
    permit = gate.observe_document("OFR/1")
    loop = FakeLoop()
    result = execute_v2_step(
        loop, synthetic_scene(), resolved(), input_arbiter=gate, input_permit=permit,
    )
    assert result.success
    assert loop.calls == 1


def test_v2_executor_does_not_run_when_human_took_over(monkeypatch):
    patched_policy(monkeypatch)
    gate = LocalInputArbiter()
    permit = gate.observe_document("OFR/1")
    gate.takeover()
    loop = FakeLoop()
    with pytest.raises(InputDenied):
        execute_v2_step(
            loop, synthetic_scene(), resolved(), input_arbiter=gate, input_permit=permit,
        )
    assert loop.calls == 0


def test_v2_executor_does_not_run_when_old_permit_used_after_release(monkeypatch):
    patched_policy(monkeypatch)
    gate = LocalInputArbiter()
    stale = gate.observe_document("OFR/1")
    gate.takeover()
    gate.release()
    loop = FakeLoop()
    with pytest.raises(InputDenied):
        execute_v2_step(
            loop, synthetic_scene(), resolved(), input_arbiter=gate, input_permit=stale,
        )
    assert loop.calls == 0


def test_v2_executor_rejects_missing_permit_when_gate_is_used(monkeypatch):
    patched_policy(monkeypatch)
    gate = LocalInputArbiter()
    loop = FakeLoop()
    with pytest.raises(ValueError, match="v2_input_permit_required"):
        execute_v2_step(loop, synthetic_scene(), resolved(), input_arbiter=gate)
    assert loop.calls == 0
