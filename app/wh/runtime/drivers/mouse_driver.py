from app.wh.runtime.drivers.base_mouse_driver import (
    BaseMouseDriver
)


class MouseDriver(
    BaseMouseDriver
):

    def move(

        self,
        x,
        y
    ):

        print(
            f"[MOUSE] move "
            f"({x}, {y})"
        )

    def click(

        self,
        x,
        y
    ):

        print(
            f"[MOUSE] click "
            f"({x}, {y})"
        )