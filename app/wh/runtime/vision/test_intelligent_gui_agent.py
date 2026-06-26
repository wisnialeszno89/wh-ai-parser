from app.wh.runtime.vision.intelligent_gui_agent import (
    IntelligentGUIAgent
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


def test_intelligent_gui_agent():

    runtime = (

        VisionRuntime()

    )

    brain = (

        ProjectBrain()

    )

    agent = (

        IntelligentGUIAgent(

            runtime,

            brain

        )

    )

    goal = (

        GUIGoal(

            "enable_rc2"

        )

    )

    assert (

        agent.execute(

            goal

        )

        is True

    )

    assert (

        brain.goal_memory.contains(

            "enable_rc2"

        )

        is True

    )

    assert (

        agent.execute(

            goal

        )

        is True

    )

    assert (

        len(

            brain.goal_memory.completed

        )

        ==

        1

    )