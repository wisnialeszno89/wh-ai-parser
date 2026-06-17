class HorizontalDivisionActionGenerator:

    def generate(

        self,

        points

    ):

        actions = []

        for point in points:

            actions.append(

                (

                    "sash_horizontal",

                    point

                )

            )

            actions.append(

                (

                    "glass_horizontal",

                    point

                )

            )

        return actions