from app.wh.runtime.vision.reflection_pattern import (
    ReflectionPattern
)


class ReflectionPatternEngine:

    def analyze(

        self,

        brain

    ):

        patterns = {}

        for reflection in (

            brain.reflection_memory.reflections

        ):

            goal_name = (

                reflection.goal_name

            )

            if goal_name not in patterns:

                patterns[goal_name] = (

                    ReflectionPattern(

                        goal_name=goal_name

                    )

                )

            pattern = (

                patterns[goal_name]

            )

            if reflection.success:

                pattern.successes += 1

            else:

                pattern.failures += 1

        return (

            list(

                patterns.values()

            )

        )