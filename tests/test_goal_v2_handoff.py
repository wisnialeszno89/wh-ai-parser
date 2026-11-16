"""V2 human handoff is timeboxed, opt-in and observes WindowHub again."""
from types import SimpleNamespace as NS

from tools import run_windowhub_goal_v2 as runner
from app.agent.runtime import goal_task_supervisor as supervisor


def test_handoff_timeout_does_not_resume(monkeypatch):
    monkeypatch.setattr(
        supervisor, "timed_salesperson_prompt",
        lambda *a, **kw: None,
    )
    recorded = []
    monkeypatch.setattr(
        supervisor, "append_unresolved_issues",
        lambda ledger: (recorded.extend(ledger.issues), len(ledger.issues))[1],
    )
    assert runner.request_human_resume(object(), timeout_seconds=60) is False
    assert len(recorded) == 1
    assert recorded[0].task == "active_goal"
    assert recorded[0].reason == "operator_timeout_dependency_unresolved"


def test_handoff_approval_requires_windowhub_refocus_and_readback(monkeypatch):
    monkeypatch.setattr(
        supervisor, "timed_salesperson_prompt",
        lambda *a, **kw: "tak",
    )
    monkeypatch.setattr(runner, "activate_windowhub_workflow_window", lambda: (True, "focused"))
    called = []
    scene = NS(observation=NS(state=NS(
        active_application="Okna.exe",
        active_window_title="Wielkość okna",
    )))
    loop = NS(observe_scene=lambda: (called.append(True), scene)[1])
    assert runner.request_human_resume(loop, timeout_seconds=60) is True
    assert called == [True]


def test_handoff_never_resumes_on_decline_or_focus_failure(monkeypatch):
    monkeypatch.setattr(
        supervisor, "timed_salesperson_prompt",
        lambda *a, **kw: "nie",
    )
    assert runner.request_human_resume(object(), timeout_seconds=60) is False
    monkeypatch.setattr(
        supervisor, "timed_salesperson_prompt",
        lambda *a, **kw: "tak",
    )
    monkeypatch.setattr(runner, "activate_windowhub_workflow_window", lambda: (False, "not found"))
    assert runner.request_human_resume(object(), timeout_seconds=60) is False
