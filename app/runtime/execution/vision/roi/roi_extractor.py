import numpy as np

from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)

from app.wh.vision.screenshot import (
    Screenshot,
)


class ROIExtractor:
    """
    Extracts image regions from GUI objects.
    """

    def extract(
        self,
        screenshot: Screenshot,
        obj: GUIObject,
    ) -> np.ndarray:

        r = obj.bounds

        return screenshot.image[
            r.top:r.bottom,
            r.left:r.right,
        ]