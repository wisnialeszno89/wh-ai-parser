class TopologyNavigator:

    def find_position(

        self,

        topology,

        field

    ):

        for row_index, row in enumerate(

            topology

        ):

            for col_index, current in enumerate(

                row

            ):

                if current == field:

                    return (

                        row_index,

                        col_index

                    )

        return None

    def left(

        self,

        topology,

        field

    ):

        row, col = self.find_position(

            topology,

            field

        )

        if col == 0:

            return None

        return topology[

            row

        ][

            col - 1

        ]

    def right(

        self,

        topology,

        field

    ):

        row, col = self.find_position(

            topology,

            field

        )

        if col == len(

            topology[row]

        ) - 1:

            return None

        return topology[

            row

        ][

            col + 1

        ]

    def top(

        self,

        topology,

        field

    ):

        row, col = self.find_position(

            topology,

            field

        )

        if row == 0:

            return None

        return topology[

            row - 1

        ][

            col

        ]

    def bottom(

        self,

        topology,

        field

    ):

        row, col = self.find_position(

            topology,

            field

        )

        if row == len(

            topology

        ) - 1:

            return None

        return topology[

            row + 1

        ][

            col

        ]