class DivisionActionGenerator:

    def generate(

        self,

        points

    ):

        actions = []

        for point in points:

            actions.append(

                (

                    "sash",

                    point

                )

            )

            actions.append(

                (

                    "glass",

                    point

                )

            )

        return actions