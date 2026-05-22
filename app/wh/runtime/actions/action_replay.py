import json

from app.wh.runtime.actions.click_action import (
    ClickAction
)
from app.wh.runtime.actions.select_tool_action_runtime import (
    SelectToolActionRuntime
)


class ActionReplay:

    @staticmethod
    def load(

        path
    ):

        with open(

            path,

            "r",

            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        actions = []

        for item in data:

            if item["type"] == "click":

                actions.append(

                    ClickAction(

                        item["x"],

                        item["y"]
                    )
                )

            elif item["type"] == "select_tool":

                actions.append(

                    SelectToolActionRuntime(

                        item["tool"]
                    )
                )

        return actions
        
    @staticmethod
    def replay(

        runtime,

        path
    ):

        actions = (
            ActionReplay.load(
                path
            )
        )

        print(
            f"[REPLAY] loaded "
            f"{len(actions)} actions"
        )

        for action in actions:

            action.execute(
                runtime
            )