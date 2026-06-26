from app.wh.runtime.vision.reflection_memory import (
    ReflectionMemory
)

from app.wh.runtime.vision.goal_reflection import (
    GoalReflection
)


def test_reflection_memory():

    memory = (

        ReflectionMemory()

    )

    memory.remember(

        GoalReflection(

            goal_name="enable_rc2",

            success=True,

            conclusion="goal_completed"

        )

    )

    assert (

        memory.count()

        ==

        1

    )

    assert (

        memory.last().goal_name

        ==

        "enable_rc2"

    )