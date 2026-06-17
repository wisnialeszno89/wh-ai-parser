from app.wh.vision.find_object import (
    FindObject
)

from app.wh.vision.screen_object import (
    ScreenObject
)


def test_find_object():

    objects = [

        ScreenObject(

            name="frame_tool.png",

            x=100,

            y=50,

            width=40,

            height=40,

            confidence=0.95

        ),

        ScreenObject(

            name="glass_tool.png",

            x=200,

            y=80,

            width=40,

            height=40,

            confidence=0.91

        )

    ]

    finder = (

        FindObject()

    )

    obj = (

        finder.find(

            objects,

            "glass_tool.png"

        )

    )

    assert obj.x == 200

    assert obj.y == 80