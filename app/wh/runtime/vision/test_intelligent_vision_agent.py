from app.wh.runtime.vision.intelligent_vision_agent import (
    IntelligentVisionAgent
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


def test_intelligent_vision_agent():

    runtime = (

        VisionRuntime()

    )

    brain = (

        ProjectBrain()

    )

    agent = (

        IntelligentVisionAgent(

            runtime,

            brain

        )

    )

    goal = (

        GUIGoal(

            "enable_rc2"

        )

    )

    result = (

        agent.execute(

            goal

        )

    )

    assert (

        result.status

        ==

        GoalExecutionStatus.SUCCESS

    )

    assert (

        brain.goal_memory.contains(

            "enable_rc2"

        )

        is True

    )

    result = (

        agent.execute(

            goal

        )

    )

    assert (

        result.status

        ==

        GoalExecutionStatus.SKIPPED

    )