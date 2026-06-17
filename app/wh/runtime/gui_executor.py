from app.wh.runtime.gui_mapper import (
    GUIMapper
)

from app.wh.runtime.gui_brain import (
    GUIBrain
)


class GUIExecutor:

    def __init__(

        self,

        mouse_enabled=False

    ):

        self.mapper = (

            GUIMapper()

        )

        self.brain = (

            GUIBrain(

                mouse_enabled=mouse_enabled

            )

        )

    def execute(

        self,

        screenshot_path,

        templates_dir,

        plan

    ):

        results = []

        for action in plan.actions:

            command = (

                self.mapper.map(

                    action

                )

            )

            result = (

                self.brain.execute(

                    screenshot_path,

                    templates_dir,

                    command

                )

            )

            results.append(

                result

            )

        return results