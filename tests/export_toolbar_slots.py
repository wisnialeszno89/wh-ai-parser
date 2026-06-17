import os
import cv2

from app.ui.detectors.extract_toolbar_slots import (
    extract_toolbar_slots
)


OUTPUT_DIR = (
    "outputs/all_slots"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


for i in range(1, 11):

    path = (
        f"samples/ui/"
        f"wh_screen_{i:02d}.png"
    )

    slots = extract_toolbar_slots(
        path,
        toolbar_x=0
    )

    for slot in slots:

        filename = (

            f"screen_{i:02d}_"

            f"slot_{slot['index']:03d}.png"
        )

        cv2.imwrite(

            os.path.join(
                OUTPUT_DIR,
                filename
            ),

            slot["crop"]
        )

print()
print(
    "[DONE]"
)
print()