from app.wh.runtime.color_registry import (
    COLORS
)


class ColorParser:

    def parse(

        self,

        text

    ):

        lower = (

            text.lower()

        )

        color_inside = ""

        color_outside = ""

        for alias, value in (

            COLORS.items()

        ):

            if alias in lower:

                color_inside = (

                    value[0]

                )

                color_outside = (

                    value[1]

                )

                break

        return (

            color_inside,

            color_outside

        )