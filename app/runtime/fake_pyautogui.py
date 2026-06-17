class Location:

    def __init__(
        self,
        x,
        y
    ):

        self.x = x

        self.y = y


class Box:

    def __init__(
        self
    ):

        self.left = 50

        self.top = 100

        self.width = 100

        self.height = 200


def locateOnScreen(

    image,

    confidence=0.9

):

    return Box()


def center(
    box
):

    return Location(

        100,

        200

    )


def click(
    x,
    y
):

    return (

        "CLICK",

        x,

        y

    )


def write(
    value
):

    return (

        "WRITE",

        value

    )