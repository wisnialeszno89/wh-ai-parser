from app.construction.construction_plan import (
    ConstructionPlan
)

from app.construction.construction_step import (
    ConstructionStep
)

from app.construction.enums.construction_action import (
    ConstructionAction
)

from app.construction.enums.plan_decision import (
    PlanDecision
)


class ConstructionPlanner:

    def build(
        self,
        construction
    ) -> ConstructionPlan:

        plan = ConstructionPlan()

        # Rama jest zawsze pierwsza
        plan.steps.append(

            ConstructionStep(

                action=ConstructionAction.CREATE_FRAME

            )

        )

        # Jeżeli są słupki
        if getattr(construction, "mullions", []):

            plan.steps.append(

                ConstructionStep(

                    action=ConstructionAction.INSERT_MULLION,

                    payload=construction.mullions

                )

            )

        # Jeżeli są segmenty (skrzydła / fixy)
        if getattr(construction, "segments", []):

            plan.steps.append(

                ConstructionStep(

                    action=ConstructionAction.INSERT_SASH,

                    field=field,

                )

            )

        # Okucia
        plan.steps.append(

            ConstructionStep(

                action=ConstructionAction.INSERT_HARDWARE

            )

        )

        # Szyby
        plan.steps.append(

            ConstructionStep(

                action=ConstructionAction.INSERT_GLASS

            )

        )

        # Zapis
        plan.steps.append(

            ConstructionStep(

                action=ConstructionAction.SAVE

            )

        )

        return plan