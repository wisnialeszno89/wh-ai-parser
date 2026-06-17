import os
import cv2

from app.ui.detectors.detect_vertical_toolbar import (
    detect_vertical_toolbar
)

from app.ui.detectors.extract_toolbar_slots import (
    extract_toolbar_slots
)


OUTPUT_DIR = "outputs/toolbar_slots"


def export_toolbar_slots(

    image_path: str
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    toolbar = detect_vertical_toolbar(
        image_path
    )

    slots = extract_toolbar_slots(

        image_path,

        toolbar_x=toolbar["x"]
    )

    for slot in slots:

        output_path = (

            f"{OUTPUT_DIR}/"
            f"slot_{slot['index']}.png"
        )

        cv2.imwrite(

            output_path,

            slot["crop"]
        )

        print(
            f"[EXPORTED] "
            f"{output_path}"
        )

    print(
        f"[DONE] "
        f"{len(slots)} slots"
    )