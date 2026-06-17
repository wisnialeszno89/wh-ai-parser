from app.wh.runtime.position_creator import (
    PositionCreator
)

from app.wh.runtime.window_builder import (
    WindowBuilder
)


class WorkflowExecutor:

    def __init__(

        self

    ):

        self.position_creator = PositionCreator()

        self.window_builder = WindowBuilder()

    def execute(

        self,

        construction

    ):

        self.position_creator.create(

            construction.width,

            construction.height

        )

        self.window_builder.build_window(

            construction

        )

        return True