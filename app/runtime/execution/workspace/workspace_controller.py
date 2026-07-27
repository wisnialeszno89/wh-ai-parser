from app.runtime.execution.click_executor import (
    ClickExecutor,
)


class WorkspaceController:

    def __init__(self):

        self.click = ClickExecutor()

    def center(
        self,
        canvas,
    ):

        return canvas.center()

    def click_center(
        self,
        canvas,
    ):

        x, y = canvas.center()

        print()
        print(
            "[WORKSPACE] Click canvas center"
        )

        self.click.click_xy(
            x,
            y,
        )

    def click(
        self,
        x: int,
        y: int,
    ):

        print()

        print(
            f"[WORKSPACE] Click ({x},{y})"
        )

        self.click.click_xy(
            x,
            y,
        )