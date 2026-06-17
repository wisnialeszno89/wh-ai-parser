import cv2

from app.ui.models.ui_object import (
    UIObject
)


MIN_SIZE = 16
MAX_SIZE = 80


def detect_tool_candidates(

    image_path: str
):

    image = cv2.imread(
        image_path
    )

    gray = cv2.cvtColor(

        image,

        cv2.COLOR_BGR2GRAY
    )

    blurred = cv2.GaussianBlur(

        gray,

        (5, 5),

        0
    )

    binary = cv2.adaptiveThreshold(

        blurred,

        255,

        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,

        cv2.THRESH_BINARY_INV,

        11,

        2
    )

    kernel = cv2.getStructuringElement(

        cv2.MORPH_RECT,

        (3, 3)
    )

    cleaned = cv2.morphologyEx(

        binary,

        cv2.MORPH_CLOSE,

        kernel
    )

    contours, _ = cv2.findContours(

        cleaned,

        cv2.RETR_EXTERNAL,

        cv2.CHAIN_APPROX_SIMPLE
    )

    objects = []

    index = 0

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if w < MIN_SIZE or h < MIN_SIZE:

            continue

        if w > MAX_SIZE or h > MAX_SIZE:

            continue

        aspect_ratio = w / h

        if aspect_ratio < 0.5:

            continue

        if aspect_ratio > 1.5:

            continue

        area = w * h

        if area < 250:

            continue

        objects.append(

            UIObject(

                id=f"tool_candidate_{index}",

                object_type="tool_candidate",

                x=x,
                y=y,

                width=w,
                height=h
            )
        )

        index += 1

    print(
        f"[DEBUG] detected candidates="
        f"{len(objects)}"
    )

    return objects