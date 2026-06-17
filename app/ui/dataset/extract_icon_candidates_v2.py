import os
import cv2


OUTPUT_DIR = (
    "outputs/icon_candidates_v2"
)


MIN_W = 12
MAX_W = 64

MIN_H = 12
MAX_H = 64

MIN_AREA = 50


def extract_icon_candidates_v2(
    image_path: str
):

    image = cv2.imread(
        image_path
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        80,
        160
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    debug = image.copy()

    for contour in contours:

        area = cv2.contourArea(
            contour
        )

        if area < MIN_AREA:
            continue

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if not (
            MIN_W <= w <= MAX_W
        ):
            continue

        if not (
            MIN_H <= h <= MAX_H
        ):
            continue

        crop = image[
            y:y+h,
            x:x+w
        ]

        candidates.append({

            "x": x,
            "y": y,

            "width": w,
            "height": h,

            "area": area,

            "crop": crop
        })

        cv2.rectangle(

            debug,

            (x, y),

            (x + w, y + h),

            (0, 255, 0),

            2
        )

    cv2.imwrite(

        "outputs/debug_icon_candidates_v2.png",

        debug
    )

    print(
        f"[CANDIDATES] "
        f"{len(candidates)}"
    )

    return candidates