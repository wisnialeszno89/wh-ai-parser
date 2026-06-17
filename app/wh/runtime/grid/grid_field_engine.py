from app.wh.runtime.fields.field import (
    Field
)


class GridFieldEngine:

    def build(

        self,

        ratio_x,

        ratio_y

    ):

        fields = []

        field_id = 1

        rows = len(

            ratio_y

        ) + 1

        cols = len(

            ratio_x

        ) + 1

        for row in range(

            rows

        ):

            for col in range(

                cols

            ):

                fields.append(

                    Field(

                        id=field_id,

                        x=col,

                        y=row

                    )

                )

                field_id += 1

        return fields