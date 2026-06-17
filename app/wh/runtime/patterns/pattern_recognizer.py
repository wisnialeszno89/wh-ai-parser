class PatternRecognizer:

    def is_single_row(

        self,

        construction

    ):

        return len(

            construction.topology

        ) == 1

    def is_single_column(

        self,

        construction

    ):

        return len(

            construction.topology[0]

        ) == 1

    def is_2x2(

        self,

        construction

    ):

        return (

            len(

                construction.topology

            ) == 2

            and

            len(

                construction.topology[0]

            ) == 2

        )

    def is_balanced(

        self,

        construction

    ):

        width = len(

            construction.topology[0]

        )

        return all(

            len(

                row

            ) == width

            for row in (

                construction.topology

            )

        )