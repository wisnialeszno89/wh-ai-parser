from app.wh.vision.screen_scene_graph import (
    ScreenSceneGraph
)


def test_screen_scene_graph():

    graph = (

        ScreenSceneGraph()

    )

    objects = (

        graph.analyze(

            "samples/ui/wh_screen_06.png",

            "templates"

        )

    )

    print()

    print(

        "===== TOP OBJECTS ====="

    )

    for obj in objects[:10]:

        print(

            f"{obj.name:<30}"

            f"{obj.confidence:.3f}"

        )

    assert len(

        objects

    ) > 0