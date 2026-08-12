from app.gui.gui_plan import (
    GuiPlan,
)

from app.gui.gui_action import (
    GuiAction,
)

from app.gui.enums.gui_tool import (
    GuiTool,
)

from app.gui.enums.gui_intent import (
    GuiIntent,
)

from app.construction.enums.construction_action import (
    ConstructionAction,
)


class GuiPlanner:

    def build(
        self,
        construction_plan,
    ) -> GuiPlan:

        gui_plan = GuiPlan()

        for step in construction_plan.steps:

            match step.action:

                case ConstructionAction.CREATE_FRAME:

                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.FRAME,
                            intent=GuiIntent.CREATE,
                        )

                    )

                case ConstructionAction.SELECT_FRAME:

                    print()
                    print("========== GUI PLANNER ==========")
                    print(step.field)
                    print("=================================")

                    # First select the already-created frame object on the canvas.
                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.FRAME,
                            intent=GuiIntent.SELECT,
                            payload=step.payload,
                        )

                    )

                    # Then edit the selected frame using the construction field.
                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.FRAME,
                            intent=GuiIntent.EDIT,
                            payload=step.payload,
                            construction_field=step.field,
                        )

                    )

                case ConstructionAction.INSERT_SASH:

                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.SASH,
                            intent=GuiIntent.CREATE,
                            payload=step.payload,
                            construction_field=step.field,
                        )

                    )

                case ConstructionAction.INSERT_MULLION:

                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.MULLION,
                            intent=GuiIntent.CREATE,
                            payload=step.payload,
                        )

                    )

                case ConstructionAction.INSERT_MOVABLE_MULLION:

                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.MOVABLE_MULLION,
                            intent=GuiIntent.CREATE,
                            payload=step.payload,
                        )

                    )

                case ConstructionAction.SELECT_GLASS:

                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.GLASS,
                            intent=GuiIntent.EDIT,
                            payload=step.payload,
                            construction_field=step.field,
                        )

                    )

                case ConstructionAction.SELECT_HARDWARE:

                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.HARDWARE,
                            intent=GuiIntent.EDIT,
                            payload=step.payload,
                            construction_field=step.field,
                        )

                    )

                case ConstructionAction.SAVE:

                    gui_plan.actions.append(

                        GuiAction(
                            tool=GuiTool.SAVE,
                            intent=GuiIntent.EDIT,
                        )

                    )

                case _:

                    pass

        return gui_plan
