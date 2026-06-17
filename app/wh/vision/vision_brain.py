from app.wh.vision.screen_scene_graph import (
    ScreenSceneGraph
)


class VisionBrain:

    def __init__(

        self,

        threshold=0.7

    ):

        self.threshold = threshold

        self.scene_graph = (

            ScreenSceneGraph()

        )

    def click(

        self,

        screenshot,

        templates_dir,

        template_name

    ):

        objects = (

            self.scene_graph.analyze(

                screenshot,

                templates_dir

            )

        )

        for obj in objects:

            if obj.name != template_name:

                continue

            if (

                obj.confidence

                <

                self.threshold

            ):

                raise RuntimeError(

                    f"{template_name} "

                    f"found with confidence "

                    f"{obj.confidence:.3f}"

                )

            center_x = (

                obj.x

                +

                obj.width // 2

            )

            center_y = (

                obj.y

                +

                obj.height // 2

            )

            return (

                center_x,

                center_y

            )

        raise RuntimeError(

            f"{template_name} not found"

        )