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

                {

                    "id": index,

                    "x": x,

                    "y": y,

                    "type": "unknown"

                }

            )

        return fields