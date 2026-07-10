import cv2

from research.gui_lab.core.panel_detector import (
    detect_panels,
)

from research.gui_lab.extractors.panel_fingerprint import (
    build_fingerprint,
)

from research.gui_lab.models.layout_model import (
    LayoutModel,
    LayoutPanel,
)


class LayoutBuilder:

    def build(
        self,
        image,
    ) -> LayoutModel:

        layout = LayoutModel()

        panels = detect_panels(
            image,
        )

        for index, panel in enumerate(
            panels,
            start=1,
        ):

            roi = image[
                panel.y:panel.y + panel.height,
                panel.x:panel.x + panel.width,
            ]

            fingerprint = build_fingerprint(
                roi,
            )

            layout.add_panel(

                LayoutPanel(

                    id=index,

                    panel=panel,

                    fingerprint=fingerprint,

                )

            )

        return layout