class DivisionPointCalculator:

    def calculate_x_points(

        self,

        construction,

        canvas

    ):

        points = []

        canvas_width = (

            canvas.right -

            canvas.left

        )

        for ratio in construction.ratio_x:

            x = int(

                canvas.left +

                canvas_width *

                ratio /

                100

            )

            points.append(

                x

            )

        return points