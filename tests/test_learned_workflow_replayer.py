from __future__ import annotations

from types import SimpleNamespace

from app.agent.agent_intent import AgentIntent
from app.agent.learning.learned_workflow import (
    LearnedAction,
    LearnedWorkflow,
    LearnedWorkflowStep,
)
from app.agent.learning.learned_workflow_replayer import (
    LearnedWorkflowReplayer,
)
from app.agent.learning.semantic_snapshot import SemanticSnapshot


class FakeControlLoop:
    def __init__(self):
        self.plan = None
        self.context = None

    def run(self, plan, context):
        self.plan = plan
        self.context = context
        return SimpleNamespace(
            success=True,
            step_results=(
                SimpleNamespace(
                    action_name="click_screen_element",
                    status=SimpleNamespace(value="completed"),
                    reason="",
                ),
            ),
        )


def _workflow():
    empty = SemanticSnapshot(
        application="WindowHub",
        window_title="Okna -",
    )

    return LearnedWorkflow(
        workflow_id="wf-1",
        name="Dodanie okna",
        application="WindowHub",
        trigger="dodaj nowe okno",
        steps=(
            LearnedWorkflowStep(
                index=1,
                action=LearnedAction(
                    name="click_screen_element",
                    target="Dodaj",
                ),
                before=empty,
                after=empty,
            ),
        ),
    )


def test_replayer_translates_learned_actions_into_normal_agent_plan():
    loop = FakeControlLoop()
    replayer = LearnedWorkflowReplayer(
        control_loop=loop,
    )

    plan = replayer.build_plan(
        _workflow()
    )

    assert plan.intent is AgentIntent.OBSERVE_WORKFLOW
    assert len(plan.steps) == 1
    assert plan.steps[0].action.name == "click_screen_element"
    assert plan.steps[0].action.target == "Dodaj"
    assert plan.steps[0].action.requires_environment_observation is True


def test_replayer_runs_workflow_through_control_loop():
    loop = FakeControlLoop()
    result = LearnedWorkflowReplayer(
        control_loop=loop,
    ).replay(
        _workflow()
    )

    assert result.success is True
    assert result.completed_steps == 1
    assert result.total_steps == 1
    assert loop.plan.steps[0].action.target == "Dodaj"
    assert loop.context.request.message == "dodaj nowe okno"


def test_learned_workflow_round_trip_from_payload():
    workflow = _workflow()

    restored = LearnedWorkflow.from_payload(
        workflow.to_payload()
    )

    assert restored == workflow


def test_replayer_derives_semantic_transition_requirements():
    before = SemanticSnapshot(
        application="WindowHub",
        window_title="Okna -",
        active_document="Dokument1",
        elements=(
            {
                "kind": "radiobutton",
                "label": "Okno",
                "uia_selected": False,
            },
        ),
    )
    after = SemanticSnapshot(
        application="WindowHub",
        window_title="Dodawanie nowej pozycji",
        active_document="Dokument1",
        elements=(
            {
                "kind": "radiobutton",
                "label": "Okno",
                "uia_selected": True,
            },
        ),
    )

    requirements = LearnedWorkflowReplayer._transition_requirements(
        before,
        after,
    )

    assert requirements == (
        {
            "kind": "radiobutton",
            "label": "Okno",
            "uia_selected": True,
        },
    )
