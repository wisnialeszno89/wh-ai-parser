import cv2
import numpy as np


MIN_SIZE = 16
MAX_SIZE = 96

MIN_CLUSTER_SIZE = 5

DISTANCE_THRESHOLD = 120


def center(rect):

    x, y, w, h = rect

    return (

        x + w // 2,

        y + h // 2
    )


def distance(a, b):

    ax, ay = center(a)

    bx, by = center(b)

    return np.sqrt(

        (ax - bx) ** 2 +

        (ay - by) ** 2
    )


def find_toolbar_regions(

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

    icon_candidates = []

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if not (
            MIN_SIZE <= w <= MAX_SIZE
        ):
            continue

        if not (
            MIN_SIZE <= h <= MAX_SIZE
        ):
            continue

        ratio = w / max(h, 1)

        if not (
            0.5 <= ratio <= 1.5
        ):
            continue

        area = w * h

        if area < 250:
            continue

        icon_candidates.append(

            (x, y, w, h)
        )

    clusters = []

    used = set()

    for i, rect in enumerate(
        icon_candidates
    ):

        if i in used:
            continue

        cluster = [rect]

        used.add(i)

        for j, other in enumerate(
            icon_candidates
        ):

            if j in used:
                continue

            if distance(
                rect,
                other
            ) < DISTANCE_THRESHOLD:

                cluster.append(
                    other
                )

                used.add(j)

        if len(cluster) >= MIN_CLUSTER_SIZE:

            clusters.append(
                cluster
            )

    toolbar_regions = []

    debug = image.copy()

    for cluster in clusters:

        xs = [

            r[0]
            for r in cluster
        ]

        ys = [

            r[1]
            for r in cluster
        ]

        ws = [

            r[0] + r[2]
            for r in cluster
        ]

        hs = [

            r[1] + r[3]
            for r in cluster
        ]

        x1 = min(xs)

        y1 = min(ys)

        x2 = max(ws)

        y2 = max(hs)

        padding = 20

        x1 = max(
            0,
            x1 - padding
        )

        y1 = max(
            0,
            y1 - padding
        )

        x2 = min(
            image.shape[1],
            x2 + padding
        )

        y2 = min(
            image.shape[0],
            y2 + padding
        )

        region = {

            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "height": y2 - y1,
            "count": len(cluster)
        }

        toolbar_regions.append(
            region
        )

        cv2.rectangle(

            debug,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            3
        )

        print()

        print(
            "[TOOLBAR]"
        )

        print(region)

    cv2.imwrite(

        "outputs/debug_toolbar_regions.png",

        debug
    )

    print()

    print(
        f"[REGIONS] "
        f"{len(toolbar_regions)}"
    )

    return toolbar_regions