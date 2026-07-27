from app.runtime.execution.keyboard.keyboard_controller import (
    KeyboardController,
)

from app.runtime.execution.interactions.interaction_types import (
    InteractionType,
)


class InteractionExecutor:

    def __init__(self):

        self.keyboard = KeyboardController()

    def execute(
        self,
        interactions,
    ):

        if not interactions:

            return

        print()
        print("=" * 60)
        print("[INTERACTIONS]")
        print("=" * 60)

        for interaction in interactions:

            print(
                f"[{interaction.type.name}] "
                f"{interaction.value or ''}"
            )

            if interaction.type == InteractionType.TAB:

                self.keyboard.press(
                    "tab",
                )

            elif interaction.type == InteractionType.ENTER:

                self.keyboard.press(
                    "enter",
                )

            elif interaction.type == InteractionType.WRITE:

                self.keyboard.write(
                    interaction.value,
                )

        print("=" * 60)