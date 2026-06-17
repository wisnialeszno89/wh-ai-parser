class WindowPlan:

    def __init__(

        self

    ):

        self.windows = []

    def add_window(

        self,

        width,

        height,

        schema

    ):

        self.windows.append(

            {

                "width": width,

                "height": height,

                "schema": schema

            }

        )