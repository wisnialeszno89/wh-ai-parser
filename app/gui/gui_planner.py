from app.gui.gui_plan import (
    GuiPlan,
)

from app.gui.gui_action import (
    GuiAction,
)

from app.gui.enums.gui_tool import (
    GuiTool,
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

                        )

                    )

                case ConstructionAction.SELECT_FRAME:

                    print()
                    print("========== GUI PLANNER ==========")
                    print(step.field)
                    print("=================================")

                    action = GuiAction(

                        tool=GuiTool.FRAME,

                        payload=step.payload,

                        construction_field=step.field,

                    )

                    print(action.construction_field)

                    gui_plan.actions.append(
                        action,
                    )

                case ConstructionAction.INSERT_SASH:

                    gui_plan.actions.append(

                        GuiAction(

                            tool=GuiTool.SASH,

                            payload=step.payload,

                            construction_field=step.field,

                        )

                    )

                case ConstructionAction.INSERT_MULLION:

                    gui_plan.actions.append(

                        GuiAction(

                            tool=GuiTool.MULLION,

                            payload=step.payload,

                        )

                    )

                case ConstructionAction.INSERT_MOVABLE_MULLION:

                    gui_plan.actions.append(

                        GuiAction(

                            tool=GuiTool.MOVABLE_MULLION,

                            payload=step.payload,

                        )

                    )

                case ConstructionAction.SELECT_GLASS:

                    gui_plan.actions.append(

                        GuiAction(

                            tool=GuiTool.GLASS,

                            payload=step.payload,

                            construction_field=step.field,

                        )

                    )

                case ConstructionAction.SELECT_HARDWARE:

                    gui_plan.actions.append(

                        GuiAction(

                            tool=GuiTool.HARDWARE,

                            payload=step.payload,

                            construction_field=step.field,

                        )

                    )

                case ConstructionAction.SAVE:

                    gui_plan.actions.append(

                        GuiAction(

                            tool=GuiTool.SAVE,

                        )

                    )

                case _:

                    pass

        return gui_plan