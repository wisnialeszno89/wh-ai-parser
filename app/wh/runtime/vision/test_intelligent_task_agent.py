from app.wh.runtime.vision.intelligent_task_agent import (
    IntelligentTaskAgent
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.vision_task import (
    VisionTask
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


def test_intelligent_task_agent():

    runtime = (

        VisionRuntime()

    )

    brain = (

        ProjectBrain()

    )

    agent = (

        IntelligentTaskAgent(

            runtime,

            brain

        )

    )

    task = (

        VisionTask(

            "configure_security"

        )

    )

    task.goals.append(

        GUIGoal(

            "enable_rc2"

        )

    )

    task.goals.append(

        GUIGoal(

            "enable_contacts"

        )

    )

    result = (

        agent.execute(

            task

        )

    )

    assert (

        result.task_name

        ==

        "configure_security"

    )

    assert (

        len(

            result.goal_results

        )

        ==

        2

    )

    assert (

        result.goal_results[0].status

        ==

        GoalExecutionStatus.SUCCESS

    )