from unittest.mock import (
    MagicMock
)

from app.wh.vision.screen_object import (
    ScreenObject
)

from app.wh.vision.vision_brain import (
    VisionBrain
)


def test_vision_brain():

    brain = VisionBrain()

    brain.scene_graph = MagicMock()

    brain.finder = MagicMock()

    brain.clicker = MagicMock()

    objects = [

        ScreenObject(

            name="glass_tool.png",

            x=100,

            y=200,

            width=40,

            height=20,

            confidence=0.95

        )

    ]

    obj = objects[0]

    brain.scene_graph.analyze.return_value = (

        objects

    )

    brain.finder.find.return_value = (

        obj

    )

    brain.clicker.click.return_value = (

        120,

        210

    )

    result = brain.click(

        "screen.png",

        "templates",

        "glass_tool.png"

    )

    assert result == (

        120,

        210

    )