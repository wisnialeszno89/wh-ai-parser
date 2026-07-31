from dataclasses import dataclass

from app.gui.gui_plan import GuiPlan


@dataclass(slots=True)
class Mission:

    name: str

    gui_plan: GuiPlan

    retry_limit: int = 3