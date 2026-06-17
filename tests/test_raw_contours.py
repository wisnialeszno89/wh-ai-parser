from app.core.debug.render_raw_contours import (
    render_raw_contours
)


IMAGE = "samples/fix_ru_window.png"

render_raw_contours(

    IMAGE,

    "outputs/debug/raw_contours.jpg"
)