from app.wh.runtime.window_builder import (
    WindowBuilder
)


class PlanExecutor:

    def __init__(

        self

    ):

        self.builder = WindowBuilder()

    def execute(

        self,

        plan

    ):

        for window in plan.windows:

            self.builder.build_window(

                window["schema"]

            )