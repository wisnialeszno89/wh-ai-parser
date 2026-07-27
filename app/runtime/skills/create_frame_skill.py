from app.runtime.skills.base_skill import (
    BaseSkill,
)


class CreateFrameSkill(BaseSkill):

    def build_actions(
        self,
        world,
        context,
    ):

        print()

        print(
            "[SKILL] CREATE FRAME"
        )

        #
        # Next sprint:
        # Build GuiActions.
        #

        return []