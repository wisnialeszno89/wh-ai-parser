from app.wh.runtime.canvas_target import (
    CanvasTarget
)

from app.wh.runtime.runtime_tool import (
    RuntimeTool
)

from app.wh.runtime.runtime_mode import (
    RuntimeMode
)

from app.wh.runtime.retry import (
    Retry
)

from app.wh.runtime.assertions import (
    RuntimeAssertions
)

from app.wh.runtime.session import (
    RuntimeSession
)

from app.wh.runtime.state.runtime_state import (
    RuntimeState
)

from app.wh.runtime.exporter import (
    RuntimeExporter
)

from app.wh.runtime.constructions.registry import (
    ConstructionRegistry
)

from app.wh.runtime.actions.models.select_tool_action import (
    SelectToolAction
)

from app.wh.runtime.actions.models.click_canvas_action import (
    ClickCanvasAction
)


class WHRuntime:

    def __init__(

        self,
        intent,
        mode=RuntimeMode.DEBUG
    ):

        self.state = RuntimeState()

        self.session = RuntimeSession(

            intent,

            mode
        )

    def log(

        self,
        message
    ):

        self.state.history.add(
            message
        )

    def attach(self):

        print(
            "[RUNTIME] attach()"
        )

        self.log(
            "attach"
        )

        self.state.connected = True

    def focus(self):

        print(
            "[RUNTIME] focus()"
        )

        self.log(
            "focus"
        )

    def new_offer(self):

        print(
            "[RUNTIME] new_offer()"
        )

        self.log(
            "new_offer"
        )

    def add_window(self):

        print(
            "[RUNTIME] add_window()"
        )

        self.log(
            "add_window"
        )

    def set_dimensions(

        self,
        width,
        height
    ):

        print(
            f"[RUNTIME] "
            f"set_dimensions "
            f"{width}x{height}"
        )

        self.log(
            f"set_dimensions("
            f"{width}x{height}"
            f")"
        )

    def select_tool(

        self,
        tool: RuntimeTool
    ):

        self.state.active_tool = tool

        print(
            f"[RUNTIME] "
            f"select_tool "
            f"{tool.value}"
        )

        self.log(
            f"select_tool("
            f"{tool.value}"
            f")"
        )

    def click_canvas(

        self,
        target: CanvasTarget
    ):

        RuntimeAssertions.assert_tool(

            self,

            self.state.active_tool
        )

        point = self.session.geometry.resolve(

            target,

            self.session.canvas_bounds
        )

        self.click_position(

            point[0],

            point[1]
        )

        print(
            f"[RUNTIME] "
            f"click_canvas "
            f"{target.value} "
            f"-> {point}"
        )

        self.log(
            f"click_canvas("
            f"{target.value}"
            f" -> {point}"
            f")"
        )

    def click_position(

        self,
        x,
        y
    ):

        if self.session.mode != RuntimeMode.DRY_RUN:

            self.session.hooks.before_click(
                f"{x},{y}"
            )

            def interaction():

                self.session.mouse.move(
                    x,
                    y
                )

                self.session.mouse.click(
                    x,
                    y
                )

                self.session.waiters.short()

            Retry.run(
                interaction
            )

            capture_name = (
                f"click_{x}_{y}"
            )

            capture_path = (
                self.session.screenshots.capture(
                    capture_name
                )
            )

            self.session.screenshot_store.add(

                name=capture_path,

                tool=(

            self.state.active_tool.value

            if self.state.active_tool

            else "unknown"
            ),

                retry=1
            )

            self.session.hooks.after_click(
                f"{x},{y}"
            )

        print(
            f"[RUNTIME] "
            f"click_position "
            f"({x}, {y})"
        )

        self.log(
            f"click_position("
            f"{x}, {y}"
            f")"
        )

    def set_glass(

        self,
        glass
    ):

        print(
            f"[RUNTIME] "
            f"set_glass "
            f"{glass}"
        )

        self.log(
            f"set_glass("
            f"{glass}"
            f")"
        )

    def set_color(

        self,
        color
    ):

        print(
            f"[RUNTIME] "
            f"set_color "
            f"{color}"
        )

        self.log(
            f"set_color("
            f"{color}"
            f")"
        )

    def save_offer(

        self,
        path="output.ofr"
    ):

        print(
            f"[RUNTIME] "
            f"save_offer "
            f"{path}"
        )

        self.log(
            f"save_offer("
            f"{path}"
            f")"
        )

        RuntimeExporter.export_actions(

            self.session,

            self.state.history
        )

    def build_geometry(

        self,
        geometry,
        intent
    ):

        builder = (
            ConstructionRegistry.resolve(
                geometry
            )
        )

        builder.build(

            self,

            intent
        )

    def execute(

        self,
        action
    ):

        if isinstance(
            action,
            SelectToolAction
        ):

            self.select_tool(
                action.tool
            )

        elif isinstance(
            action,
            ClickCanvasAction
        ):

            self.click_canvas(
                action.target
            )

        else:

            raise RuntimeError(
                f"Unknown action: "
                f"{action}"
            )