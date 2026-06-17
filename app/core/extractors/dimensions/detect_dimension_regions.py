import cv2


LINE_THRESHOLD = 25
HORIZONTAL_GAP = 50


def detect_dimension_regions(image_path: str):

    image = cv2.imread(
        image_path
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    blur = cv2.GaussianBlur(

        gray,

        (5, 5),

        0
    )

    thresh = cv2.adaptiveThreshold(

        blur,

        255,

        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,

        cv2.THRESH_BINARY_INV,

        11,

        2
    )

    contours, _ = cv2.findContours(

        thresh,

        cv2.RETR_EXTERNAL,

        cv2.CHAIN_APPROX_SIMPLE
    )

    raw_regions = []

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if w < 8:
            continue

        if h < 8:
            continue

        if w > 80:
            continue

        if h > 80:
            continue

        raw_regions.append(
            (x, y, w, h)
        )

    raw_regions = sorted(
        raw_regions,
        key=lambda r: (r[1], r[0])
    )

    groups = []

    for region in raw_regions:

        x, y, w, h = region

        added = False

        for group in groups:

            gx, gy, gw, gh = group

            same_line = (
                abs(y - gy) < LINE_THRESHOLD
            )

            close_horizontal = (
                abs(x - (gx + gw)) < HORIZONTAL_GAP
            )

            if same_line and close_horizontal:

                new_x = min(gx, x)

                new_y = min(gy, y)

                new_w = max(
                    gx + gw,
                    x + w
                ) - new_x

                new_h = max(
                    gy + gh,
                    y + h
                ) - new_y

                group[0] = new_x
                group[1] = new_y
                group[2] = new_w
                group[3] = new_h

                added = True

                break

        if not added:

            groups.append(
                [x, y, w, h]
            )

    return [

        tuple(group)

        for group in groups
    ]