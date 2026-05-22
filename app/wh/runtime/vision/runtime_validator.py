from app.wh.runtime.recovery.failure_type import (
    FailureType
)


class RuntimeValidator:

    attempts = 0

    @staticmethod
    def validate_click(

        runtime,
        x,
        y
    ):

        RuntimeValidator.attempts += 1

        print(
            f"[VISION] validate click "
            f"{x},{y}"
        )

        if RuntimeValidator.attempts == 1:

            print(
                "[VISION] simulated failure"
            )

            return (

                False,

                FailureType.TOOL_NOT_ACTIVE
            )

        print(
            "[VISION] validation ok"
        )

        return (

            True,

            None
        )