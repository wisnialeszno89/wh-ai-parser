from app.wh.runtime.vision.vision_action import (
    VisionAction
)


class VisionActionFactory:

    def create(

        self,

        goal

    ):

        return (

            VisionAction(

                name=goal.name,

                template_path=(

                    f"templates/{goal.name}.png"

                )

            )

        )