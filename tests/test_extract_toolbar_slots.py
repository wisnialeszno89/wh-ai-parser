from app.ui.detectors.detect_vertical_toolbar import (
    detect_vertical_toolbar
)

from app.ui.detectors.extract_toolbar_slots import (
    extract_toolbar_slots
)


IMAGE = "samples/wh_screen.png"


toolbar = detect_vertical_toolbar(
    IMAGE
)


extract_toolbar_slots(

    IMAGE,

    toolbar_x=toolbar["x"]
)