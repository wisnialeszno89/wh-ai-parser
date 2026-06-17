import cv2

from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine
)

from app.wh.vision.screen_scene_graph import (
    ScreenSceneGraph
)


def test_draw_matches():

    screenshot = (

        MSSScreenshotEngine()

        .capture()

    )

    image = screenshot.image

    if (

        len(image.shape) == 3

        and

        image.shape[2] == 4

    ):

        image = cv2.cvtColor(

            image,

            cv2.COLOR_BGRA2BGR

        )

    graph = (

        ScreenSceneGraph()

    )

    objects = (

        graph.analyze(

            screenshot,

            "templates"

        )

    )

    for obj in objects:

        print(

            f"{obj.name:<35}"

            f"{obj.confidence:.3f}"

        )

        if obj.confidence > 0.5:

            cv2.rectangle(

                image,

                (obj.x, obj.y),

                (

                    obj.x + obj.width,

                    obj.y + obj.height

                ),

                (0, 255, 0),

                2

            )

            cv2.putText(

                image,

                obj.name,

                (

                    obj.x,

                    obj.y - 10

                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.5,

                (0, 255, 0),

                1

            )

    cv2.imwrite(

        "samples/matches.png",

        image

    )