from app.wh.runtime.recovery.failure_type import (
    FailureType
)

from app.wh.runtime.runtime_tool import (
    RuntimeTool
)


class RecoveryManager:

    @staticmethod
    def recover(

        runtime,
        attempt,
        failure_type
    ):

        print(
            f"[RECOVERY] "
            f"{failure_type} "
            f"attempt {attempt}"
        )

        if failure_type == (
            FailureType.CLICK_MISS
        ):

            if attempt == 1:

                print(
                    "[RECOVERY] small offset"
                )

                return 5

            if attempt == 2:

                print(
                    "[RECOVERY] reverse offset"
                )

                return -5

        if failure_type == (
            FailureType.TOOL_NOT_ACTIVE
        ):

            print(
                "[RECOVERY] reselect glass tool"
            )

            runtime.select_tool(
                RuntimeTool.GLASS
            )

            return 0

        if failure_type == (
            FailureType.MENU_NOT_OPENED
        ):

            print(
                "[RECOVERY] reopen menu"
            )

            return 0

        print(
            "[RECOVERY] no strategy"
        )

        return 0