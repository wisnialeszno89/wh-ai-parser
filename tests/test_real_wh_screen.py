from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine
)

from app.wh.vision.screen_scene_graph import (
    ScreenSceneGraph
)


def test_real_wh_screen():

    screen = (

        MSSScreenshotEngine()

        .capture()

    )

    graph = (

        ScreenSceneGraph()

    )

    objects = (

        graph.analyze(

            screen,

            "templates"

        )

    )

    print()

    for obj in objects:

        print(

            f"{obj.name:<35}"

            f"{obj.confidence:.3f}"

        )

    assert len(

        objects

    ) > 0