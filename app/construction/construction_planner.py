from app.construction.construction_plan import (
    ConstructionPlan,
)

from app.construction.construction_step import (
    ConstructionStep,
)

from app.construction.enums.construction_action import (
    ConstructionAction,
)

from app.construction.models.component_selection import (
    ComponentSelection,
)


class ConstructionPlanner:

    def build(
        self,
        construction,
    ) -> ConstructionPlan:

        plan = ConstructionPlan()

        #
        # Create frame.
        #

        plan.steps.append(

            ConstructionStep(

                action=ConstructionAction.CREATE_FRAME,

            )

        )

        for field in construction.fields:

            #
            # Frame.
            #

            if field.frame:

                plan.steps.append(

                    ConstructionStep(

                        action=ConstructionAction.SELECT_FRAME,

                        payload=ComponentSelection(

                            category="FRAME",

                            database_key=field.frame,

                        ),

                        field=field,

                    )

                )

            #
            # Sash.
            #

            plan.steps.append(

                ConstructionStep(

                    action=ConstructionAction.INSERT_SASH,

                    field=field,

                )

            )

            #
            # Glass.
            #

            if field.glass:

                plan.steps.append(

                    ConstructionStep(

                        action=ConstructionAction.SELECT_GLASS,

                        payload=ComponentSelection(

                            category="GLASS",

                            database_key=field.glass,

                        ),

                        field=field,

                    )

                )

            #
            # Hardware.
            #

            if field.hardware:

                plan.steps.append(

                    ConstructionStep(

                        action=ConstructionAction.SELECT_HARDWARE,

                        payload=ComponentSelection(

                            category="HARDWARE",

                            database_key=field.hardware,

                        ),

                        field=field,

                    )

                )

            #
            # Extension.
            #

            if field.extension:

                plan.steps.append(

                    ConstructionStep(

                        action=ConstructionAction.SELECT_EXTENSION,

                        payload=ComponentSelection(

                            category="EXTENSION",

                            database_key=field.extension,

                        ),

                        field=field,

                    )

                )

        #
        # Save.
        #

        plan.steps.append(

            ConstructionStep(

                action=ConstructionAction.SAVE,

            )

        )

        return plan