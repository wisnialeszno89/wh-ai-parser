class HorizontalDivisionPointCalculator:

    def calculate_y_points(

        self,

        construction,

        canvas

    ):

        points = []

        canvas_height = (

            canvas.bottom -

            canvas.top

        )

        for ratio in construction.ratio_y:

            y = int(

                canvas.top +

                canvas_height *

                ratio /

                100

            )

            points.append(

                y

            )

        return points