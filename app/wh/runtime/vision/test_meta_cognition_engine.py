from app.wh.runtime.vision.meta_cognition_engine import (
    MetaCognitionEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.goal_reflection import (
    GoalReflection
)


def test_meta_cognition_engine():

    brain = (

        ProjectBrain()

    )

    brain.reflection_memory.remember(

        GoalReflection(

            goal_name="enable_rc2",

            success=True,

            conclusion="goal_completed"

        )

    )

    brain.reflection_memory.remember(

        GoalReflection(

            goal_name="enable_contacts",

            success=False,

            conclusion="goal_failed"

        )

    )

    engine = (

        MetaCognitionEngine()

    )

    insight = (

        engine.analyze(

            brain

        )

    )

    assert (

        insight.total_reflections

        ==

        2

    )

    assert (

        insight.total_successes

        ==

        1

    )

    assert (

        insight.total_failures

        ==

        1

    )

    assert (

        insight.success_rate

        ==

        0.5

    )