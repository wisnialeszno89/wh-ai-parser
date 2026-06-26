from copy import deepcopy


class GeometryOptimizer:

    def optimize(

        self,

        project

    ):

        optimized = (

            deepcopy(

                project

            )

        )

        width = (

            optimized.schema.width

        )

        if width > 4000:

            optimized.schema.division = (

                True

            )

            optimized.schema.division_type = (

                "vertical"

            )

            optimized.schema.ratio_x = [

                0.5

            ]

        return optimized