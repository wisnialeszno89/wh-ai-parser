from types import SimpleNamespace

from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import (
    LearnedAction,
    LearnedWorkflow,
    LearnedWorkflowStep,
)
from app.agent.learning.learned_workflow_replayer import LearnedWorkflowReplayer
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
                    action_name=plan.steps[0].action.name,
                    status=SimpleNamespace(value="completed"),
                    reason="",
                ),
            ),
        )


def test_replayer_applies_parameter_override_to_write_text_action():
    snapshot = SemanticSnapshot(
        application="WindowHub",
        window_title="Nowe okno",
    )
    workflow = LearnedWorkflow(
        workflow_id="wf-parameter",
        name="Nowe okno z wymiarem",
        application="WindowHub",
        trigger="dodaj nowe okno",
        steps=(
            LearnedWorkflowStep(
                index=1,
                action=LearnedAction(
                    name="write_text",
                    target="Szerokość",
                    value="1200",
                    value_source="parameter",
                    parameter_name="szerokosc",
                ),
                before=snapshot,
                after=snapshot,
            ),
        ),
    )

    loop = FakeControlLoop()

    result = LearnedWorkflowReplayer(
        control_loop=loop,
    ).replay(
        workflow,
        parameters={"width": 1350},
    )

    assert result.success is True
    assert loop.plan.steps[0].action.name == "write_text"
    assert loop.plan.steps[0].action.target == "Szerokość"
    assert loop.plan.steps[0].action.value == "1350"
