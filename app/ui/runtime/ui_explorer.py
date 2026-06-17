import cv2


MIN_W = 12
MAX_W = 120

MIN_H = 12
MAX_H = 120

MIN_AREA = 50


def ui_explorer(
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

    controls = []

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

        controls.append({

            "type": "control",

            "x": x,
            "y": y,

            "width": w,
            "height": h,

            "area": area
        })

        cv2.rectangle(

            debug,

            (x, y),

            (x + w, y + h),

            (0, 255, 0),

            2
        )

    cv2.imwrite(

        "outputs/ui_explorer_debug.png",

        debug
    )

    print()
    print(
        f"[CONTROLS] "
        f"{len(controls)}"
    )
    print()

    return controls