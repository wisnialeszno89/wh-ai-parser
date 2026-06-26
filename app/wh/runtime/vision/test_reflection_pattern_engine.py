from app.wh.runtime.vision.reflection_pattern_engine import (
    ReflectionPatternEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.goal_reflection import (
    GoalReflection
)


def test_reflection_pattern_engine():

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

            goal_name="enable_rc2",

            success=True,

            conclusion="goal_completed"

        )

    )

    brain.reflection_memory.remember(

        GoalReflection(

            goal_name="enable_rc2",

            success=False,

            conclusion="goal_failed"

        )

    )

    engine = (

        ReflectionPatternEngine()

    )

    patterns = (

        engine.analyze(

            brain

        )

    )

    assert (

        len(

            patterns

        )

        ==

        1

    )

    assert (

        patterns[0].goal_name

        ==

        "enable_rc2"

    )

    assert (

        patterns[0].successes

        ==

        2

    )

    assert (

        patterns[0].failures

        ==

        1

    )