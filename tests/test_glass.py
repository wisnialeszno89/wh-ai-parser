from app.knowledge.glass.glass import (
    Glass
)


def test_glass():

    glass = Glass(

        ug=0.5,

        panes=3

    )

    assert glass.ug == 0.5

    assert glass.panes == 3