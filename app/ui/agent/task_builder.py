from app.ui.agent.task_schema import (
    Task
)


def build_tasks(
    construction
):

    tasks = []

    tasks.append(

        Task(

            task="create_construction",

            params={}
        )
    )

    if (

        construction.get(
            "width_mm"
        )

        and

        construction.get(
            "height_mm"
        )

    ):

        tasks.append(

            Task(

                task="set_dimensions",

                params={

                    "width":

                    construction[
                        "width_mm"
                    ],

                    "height":

                    construction[
                        "height_mm"
                    ]
                }
            )
        )

    if construction.get(
        "segments"
    ):

        tasks.append(

            Task(

                task="build_segments",

                params={

                    "segments":

                    construction[
                        "segments"
                    ]
                }
            )
        )

    if construction.get(
        "profile_system"
    ):

        tasks.append(

            Task(

                task="configure_profile",

                params={

                    "profile":

                    construction[
                        "profile_system"
                    ]
                }
            )
        )

    if construction.get(
        "glass_type"
    ):

        tasks.append(

            Task(

                task="configure_glass",

                params={

                    "glass":

                    construction[
                        "glass_type"
                    ]
                }
            )
        )

    return tasks