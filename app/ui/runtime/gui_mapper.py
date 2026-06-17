import cv2


MIN_W = 16
MIN_H = 16

MAX_W = 600
MAX_H = 200


def gui_mapper(
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
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    controls = []

    debug = image.copy()

    for contour in contours:

        area = cv2.contourArea(
            contour
        )

        if area < 50:
            continue

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if w < MIN_W:
            continue

        if h < MIN_H:
            continue

        if w > MAX_W:
            continue

        if h > MAX_H:
            continue

        element_type = "control"

        ratio = w / max(h, 1)

        if ratio > 4:

            element_type = "toolbar"

        elif 0.8 <= ratio <= 1.2:

            element_type = "icon"

        elif ratio > 1.5:

            element_type = "button"

        controls.append({

            "type": element_type,

            "x": x,
            "y": y,

            "width": w,
            "height": h,

            "area": area
        })

        color = {

            "icon": (0, 255, 0),

            "button": (255, 255, 0),

            "toolbar": (0, 0, 255),

            "control": (255, 0, 0)

        }.get(
            element_type,
            (255, 255, 255)
        )

        cv2.rectangle(

            debug,

            (x, y),

            (x + w, y + h),

            color,

            2
        )

    cv2.imwrite(

        "outputs/gui_mapper_debug.png",

        debug
    )

    print()

    print(
        f"[ELEMENTS] "
        f"{len(controls)}"
    )

    print()

    return controls