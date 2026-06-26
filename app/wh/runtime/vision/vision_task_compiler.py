from app.wh.runtime.vision.vision_task import (
    VisionTask
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.task_library import (
    CONFIGURE_SECURITY,
    CONFIGURE_HARDWARE
)


class VisionTaskCompiler:

    def compile(

        self,

        offer

    ):

        tasks = []

        if (

            offer.security.rc2

            or

            offer.security.contacts

        ):

            task = (

                VisionTask(

                    CONFIGURE_SECURITY

                )

            )

            if (

                offer.security.rc2

            ):

                task.goals.append(

                    GUIGoal(

                        "enable_rc2"

                    )

                )

            if (

                offer.security.contacts

            ):

                task.goals.append(

                    GUIGoal(

                        "enable_contacts"

                    )

                )

            tasks.append(

                task

            )

        if (

            offer.hardware.hidden_hinges

            or

            offer.hardware.v_perfect

        ):

            task = (

                VisionTask(

                    CONFIGURE_HARDWARE

                )

            )

            if (

                offer.hardware.hidden_hinges

            ):

                task.goals.append(

                    GUIGoal(

                        "enable_hidden_hinges"

                    )

                )

            if (

                offer.hardware.v_perfect

            ):

                task.goals.append(

                    GUIGoal(

                        "enable_v_perfect"

                    )

                )

            tasks.append(

                task

            )

        return tasks