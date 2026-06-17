from app.wh.input.mouse import (
    Mouse
)


class ClickObject:

    def __init__(

        self,

        mouse_enabled=False

    ):

        self.mouse = (

            Mouse(

                enabled=mouse_enabled

            )

        )

    def click(

        self,

        obj

    ):

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

        self.mouse.click(

            center_x,

            center_y

        )

        return (

            center_x,

            center_y

        )