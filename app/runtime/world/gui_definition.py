from dataclasses import dataclass

from app.runtime.world.gui_region import GuiRegion


@dataclass(slots=True)
class GuiDefinition:

    region: GuiRegion

    template: str | None = None

    confidence: float = 0.90