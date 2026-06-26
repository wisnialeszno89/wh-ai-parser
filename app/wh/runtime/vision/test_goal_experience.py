from app.wh.runtime.vision.goal_experience import (
    GoalExperience
)

from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)


def test_goal_experience():

    experience = (

        GoalExperience(

            goal_name="enable_rc2",

            level=(

                GoalExperienceLevel.HIGH

            ),

            total_executions=25

        )

    )

    assert (

        experience.goal_name

        ==

        "enable_rc2"

    )

    assert (

        experience.level

        ==

        GoalExperienceLevel.HIGH

    )

    assert (

        experience.total_executions

        ==

        25

    )