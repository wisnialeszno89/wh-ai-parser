from app.gui.gui_plan import (
    GuiPlan
)


class ConsoleRuntime:

    def execute(
        self,
        gui_plan: GuiPlan
    ):

        print()

        print("=" * 40)
        print("      WH AI AGENT")
        print("=" * 40)

        for action in gui_plan.actions:

            print(
                f"{action.tool.name}"
            )

            if action.payload:

                print(
                    f"   -> {action.payload}"
                )

        print("=" * 40)
        print("SUCCESS")
        print("=" * 40)