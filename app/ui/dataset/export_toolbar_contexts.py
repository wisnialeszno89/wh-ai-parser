import os
import cv2


OUTPUT_DIR = "outputs/toolbar_contexts"

WINDOW_SIZE = 96
STEP = 24

TOP_K = 20

TOOLBAR_MAX_Y = 120

AUTO_SAVE_THRESHOLD = 0.50


def export_toolbar_contexts(

    image_path: str,

    template_path: str,

    template_name: str
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    dataset_dir = (
        f"dataset/{template_name}"
    )

    os.makedirs(
        dataset_dir,
        exist_ok=True
    )

    image = cv2.imread(
        image_path
    )

    template = cv2.imread(
        template_path
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    template_gray = cv2.cvtColor(
        template,
        cv2.COLOR_BGR2GRAY
    )

    template_gray = cv2.resize(
        template_gray,
        (24, 24)
    )

    height, width = gray.shape

    matches = []

    for y in range(
    0,
    TOOLBAR_MAX_Y,
    STEP
    ):

        for x in range(
            0,
            width - 24,
            STEP
        ):

            icon_crop = gray[
                y:y + 24,
                x:x + 24
            ]

            result = cv2.matchTemplate(
                icon_crop,
                template_gray,
                cv2.TM_CCOEFF_NORMED
            )

            _, score, _, _ = cv2.minMaxLoc(
                result
            )

            matches.append({

                "x": x,
                "y": y,
                "score": score
            })

    matches = sorted(
        matches,
        key=lambda m: m["score"],
        reverse=True
    )

    top_matches = matches[:TOP_K]

    saved = 0

    for index, match in enumerate(top_matches):

        center_x = match["x"] + 12
        center_y = match["y"] + 12

        x1 = max(
            0,
            center_x - WINDOW_SIZE // 2
        )

        y1 = max(
            0,
            center_y - WINDOW_SIZE // 2
        )

        x2 = min(
            width,
            x1 + WINDOW_SIZE
        )

        y2 = min(
            height,
            y1 + WINDOW_SIZE
        )

        context_crop = image[
            y1:y2,
            x1:x2
        ]

        output_path = (
            f"{OUTPUT_DIR}/"
            f"{template_name}_{index}.png"
        )

        cv2.imwrite(
            output_path,
            context_crop
        )

        print(
        f"[CONTEXT MATCH] "
        f"{template_name} "
        f"{match['score']}"
        )

        print(
        f"x={match['x']} "
        f"y={match['y']}"
        )
        

        if match["score"] >= AUTO_SAVE_THRESHOLD:

            dataset_path = (
                f"{dataset_dir}/"
                f"{template_name}_{index}.png"
            )

            cv2.imwrite(
                dataset_path,
                context_crop
            )

            saved += 1

    print(
        f"[SAVED CONTEXTS] "
        f"{template_name} "
        f"=> "
        f"{saved}"
    )