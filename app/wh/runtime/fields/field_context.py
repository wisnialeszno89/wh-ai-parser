class FieldContext:

    def __init__(

        self,

        field,

        topology_context

    ):

        self.field = field

        self.topology_context = (

            topology_context

        )

    def left(

        self

    ):

        return (

            self.topology_context.left(

                self.field

            )

        )

    def right(

        self

    ):

        return (

            self.topology_context.right(

                self.field

            )

        )

    def top(

        self

    ):

        return (

            self.topology_context.top(

                self.field

            )

        )

    def bottom(

        self

    ):

        return (

            self.topology_context.bottom(

                self.field

            )

        )