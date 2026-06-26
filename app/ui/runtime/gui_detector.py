from app.ui.runtime.find_toolbar_band import (
    find_toolbar_band
)

from app.ui.models.gui_model import (
    GuiModel
)


class GuiDetector:

    def detect(
        self,
        image
    ) -> GuiModel:

        toolbars = find_toolbar_band(
            image
        )

        gui = GuiModel()

        gui.toolbars = toolbars

        if toolbars:

            gui.primary_toolbar = toolbars[0]

        return gui