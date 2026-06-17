import cv2


SLOT_HEIGHT = 38
SLOT_WIDTH = 38


def extract_toolbar_slots(

    image_path: str,

    toolbar_x: int
):

    image = cv2.imread(
        image_path
    )

    height, width = image.shape[:2]

    slots = []

    start_y = 70

    end_y = height - 90

    current_y = start_y

    index = 0

    debug = image.copy()

    while current_y < end_y:

        x1 = max(
            0,
            toolbar_x - 4
        )

        y1 = current_y

        x2 = min(
            width,
            x1 + SLOT_WIDTH
        )

        y2 = min(
            height,
            y1 + SLOT_HEIGHT
        )

        crop = image[
            y1:y2,
            x1:x2
        ]

        slots.append({

            "index": index,

            "x": x1,
            "y": y1,

            "width": SLOT_WIDTH,
            "height": SLOT_HEIGHT,

            "crop": crop
        })

        cv2.rectangle(

            debug,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            2
        )

        current_y += SLOT_HEIGHT

        index += 1

    output_path = (
        "outputs/debug_toolbar_slots.png"
    )

    cv2.imwrite(
        output_path,
        debug
    )

    print(
        f"[SLOTS] "
        f"{len(slots)}"
    )

    print(
        f"[SAVED] "
        f"{output_path}"
    )

    return slots