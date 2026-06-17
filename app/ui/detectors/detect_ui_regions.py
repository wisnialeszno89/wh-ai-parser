import os
import cv2
import numpy as np


OUTPUT_PATH = (
    "outputs/debug_ui_regions.png"
)


MIN_AREA = 3000


def detect_ui_regions(

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

    kernel = np.ones(

        (5, 5),

        np.uint8
    )

    dilated = cv2.dilate(

        edges,

        kernel,

        iterations=2
    )

    contours, _ = cv2.findContours(

        dilated,

        cv2.RETR_EXTERNAL,

        cv2.CHAIN_APPROX_SIMPLE
    )

    debug = image.copy()

    regions = []

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        if area < MIN_AREA:
            continue

        crop = gray[
            y:y+h,
            x:x+w
        ]

        local_edges = cv2.Canny(

            crop,

            80,

            160
        )

        local_contours, _ = cv2.findContours(

            local_edges,

            cv2.RETR_LIST,

            cv2.CHAIN_APPROX_SIMPLE
        )

        small_objects = 0

        long_lines = 0

        for c in local_contours:

            a = cv2.contourArea(c)

            x2, y2, w2, h2 = cv2.boundingRect(c)

            if 20 <= a <= 800:

                small_objects += 1

            if w2 > 80 or h2 > 80:

                long_lines += 1

        score = (

            small_objects
            -
            (long_lines * 10)
        )

        regions.append({

            "x": x,

            "y": y,

            "w": w,

            "h": h,

            "score": score
        })

    regions = sorted(

        regions,

        key=lambda r: r["score"],

        reverse=True
    )

    top_regions = regions[:15]

    for region in top_regions:

        x = region["x"]

        y = region["y"]

        w = region["w"]

        h = region["h"]

        cv2.rectangle(

            debug,

            (x, y),

            (x + w, y + h),

            (0, 255, 0),

            2
        )

        print(

            f"[UI REGION] "

            f"x={x} "

            f"y={y} "

            f"w={w} "

            f"h={h} "

            f"score={region['score']}"
        )

    os.makedirs(

        "outputs",

        exist_ok=True
    )

    cv2.imwrite(

        OUTPUT_PATH,

        debug
    )

    print(
        f"[SAVED] {OUTPUT_PATH}"
    )

    return top_regions