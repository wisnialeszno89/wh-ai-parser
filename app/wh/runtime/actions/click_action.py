from app.wh.runtime.actions.base_action import (
    BaseAction
)

from app.wh.runtime.vision.runtime_validator import (
    RuntimeValidator
)

from app.wh.runtime.recovery.recovery_manager import (
    RecoveryManager
)


class ClickAction(

    BaseAction
):

    def __init__(

        self,
        x,
        y
    ):

        self.x = x

        self.y = y

    def execute(

        self,
        runtime
    ):

        max_attempts = 3

        for attempt in range(

            1,

            max_attempts + 1
        ):

            print(
                f"[ACTION] click attempt "
                f"{attempt}/"
                f"{max_attempts}"
            )

            success, failure_type = (

                self.validate(
                    runtime
                )
            )

            offset_x = (
                RecoveryManager.recover(

                    runtime,

                    attempt,

                    failure_type
                )
            )

            runtime.click_position(

                self.x + offset_x,

                self.y
            )

            if success:

                print(
                    "[ACTION] click success"
                )

                return

            print(
                "[ACTION] retry click"
            )

        raise RuntimeError(

            f"Click validation failed: "

            f"{self.x}, {self.y}"
        )

    def validate(

        self,
        runtime
    ):

        return RuntimeValidator.validate_click(

            runtime,

            self.x,

            self.y
        )

    def serialize(

        self
    ):

        return {

            "type": "click",

            "x": self.x,

            "y": self.y
        }