from dataclasses import dataclass, field

from app.gui.models.screen_element import (
    ScreenElement
)


@dataclass
class GuiKnowledge:

    elements: dict = field(
        default_factory=dict
    )

    def register(

        self,

        tool,

        element: ScreenElement

    ):

        self.elements[tool] = element

    def get(

        self,

        tool

    ):

        return self.elements.get(tool)