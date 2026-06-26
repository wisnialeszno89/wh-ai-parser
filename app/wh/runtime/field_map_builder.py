from app.wh.runtime.field import (
    Field
)


class FieldMapBuilder:

    def build(

        self,

        grid

    ):

        fields = []

        for index, (x, y) in enumerate(

            grid,

            start=1

        ):

            fields.append(

                Field(

                    id=index,

                    x=x,

                    y=y

                )

            )

        return fields