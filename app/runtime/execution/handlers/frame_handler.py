from app.runtime.execution.handlers.base_handler import (
    BaseHandler,
)

from app.runtime.execution.handlers.handler_context import (
    HandlerContext,
)

from app.runtime.execution.interactions.interaction_plan import (
    InteractionPlan,
)

from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)

from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)

from app.runtime.execution.interactions.interaction_target import (
    InteractionTarget,
)


class FrameHandler(BaseHandler):

    def execute(
        self,
        context: HandlerContext,
        payload,
    ) -> InteractionPlan:

        field = context.action.construction_field

        if field is None:

            raise RuntimeError(
                "FrameHandler requires construction_field"
            )

        plan = InteractionPlan()

        #
        # Width
        #

        plan.steps.append(

            InteractionStep(

                action=InteractionAction.CLICK,

                target=InteractionTarget.FRAME_WIDTH,

            )

        )

        plan.steps.append(

            InteractionStep(

                action=InteractionAction.WRITE,

                value=str(field.width),

            )

        )

        plan.steps.append(

            InteractionStep(

                action=InteractionAction.VERIFY,

                target=InteractionTarget.FRAME_WIDTH,

                value=str(field.width),

            )

        )

        #
        # Height
        #

        plan.steps.append(

            InteractionStep(

                action=InteractionAction.CLICK,

                target=InteractionTarget.FRAME_HEIGHT,

            )

        )

        plan.steps.append(

            InteractionStep(

                action=InteractionAction.WRITE,

                value=str(field.height),

            )

        )

        plan.steps.append(

            InteractionStep(

                action=InteractionAction.VERIFY,

                target=InteractionTarget.FRAME_HEIGHT,

                value=str(field.height),

            )

        )

        return plan