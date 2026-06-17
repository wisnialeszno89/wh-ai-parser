class DivisionPointCalculator:

    def calculate_x_points(

        self,

        construction

    ):

        points = []

        for ratio in construction.ratio_x:

            x = int(

                construction.width

                *

                ratio

                /

                100

            )

            points.append(

                x

            )

        return points