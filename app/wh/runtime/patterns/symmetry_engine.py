class SymmetryEngine:

    def is_horizontal_symmetric(

        self,

        construction

    ):

        topology = (

            construction.topology

        )

        return topology == list(

            reversed(

                topology

            )

        )

    def is_vertical_symmetric(

        self,

        construction

    ):

        topology = (

            construction.topology

        )

        mirrored = []

        for row in topology:

            mirrored.append(

                list(

                    reversed(

                        row

                    )

                )

            )

        return topology == mirrored