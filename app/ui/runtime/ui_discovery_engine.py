import cv2


GRID_STEP = 40


def ui_discovery_engine(
    image_path: str
):

    image = cv2.imread(
        image_path
    )

    height, width = image.shape[:2]

    points = []

    debug = image.copy()

    index = 0

    for y in range(

        20,
        height,
        GRID_STEP

    ):

        for x in range(

            20,
            width,
            GRID_STEP

        ):

            points.append({

                "id": index,

                "x": x,

                "y": y
            })

            cv2.circle(

                debug,

                (x, y),

                2,

                (0, 255, 0),

                -1
            )

            index += 1

    cv2.imwrite(

        "outputs/ui_discovery_grid.png",

        debug
    )

    print()

    print(
        f"[DISCOVERY POINTS] "
        f"{len(points)}"
    )

    print()

    return points