class GridDivisionEngine:

    def build_grid(

        self,

        x_points,

        y_points

    ):

        fields = []

        for y in y_points:

            for x in x_points:

                fields.append(

                    (

                        x,

                        y

                    )

                )

        return fields