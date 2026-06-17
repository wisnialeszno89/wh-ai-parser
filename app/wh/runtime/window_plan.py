from app.wh.runtime.construction_schema import (
    ConstructionSchema
)


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

            ConstructionSchema(

                width=width,

                height=height,

                schema=schema

            )

        )