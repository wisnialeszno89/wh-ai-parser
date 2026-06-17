class ConstructionContext:

    def __init__(

        self,

        construction

    ):

        self.construction = (

            construction

        )

    def field(

        self,

        field_id

    ):

        for field in (

            self.construction.fields

        ):

            if field.id == field_id:

                return field

        return None

    def top_left(

        self

    ):

        return (

            self.construction.topology[0][0]

        )

    def top_right(

        self

    ):

        return (

            self.construction.topology[0][-1]

        )

    def bottom_left(

        self

    ):

        return (

            self.construction.topology[-1][0]

        )

    def bottom_right(

        self

    ):

        return (

            self.construction.topology[-1][-1]

        )

    def row(

        self,

        index

    ):

        return (

            self.construction.topology[index]

        )

    def column(

        self,

        index

    ):

        column = []

        for row in (

            self.construction.topology

        ):

            column.append(

                row[index]

            )

        return column