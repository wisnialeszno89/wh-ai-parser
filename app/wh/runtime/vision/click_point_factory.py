from app.wh.runtime.vision.click_point import (
    ClickPoint
)


class ClickPointFactory:

    def create(

        self,

        match_result

    ):

        return ClickPoint(

            x=match_result.x,

            y=match_result.y

        )