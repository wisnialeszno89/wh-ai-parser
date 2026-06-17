import os
import cv2


OUTPUT_DIR = (
    "outputs/semantic_candidates"
)

WINDOW = 38
STEP = 20


def extract_semantic_candidates(
    image_path: str
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    image = cv2.imread(
        image_path
    )

    height, width = image.shape[:2]

    index = 0

    for y in range(
        0,
        height - WINDOW,
        STEP
    ):

        for x in range(
            0,
            width - WINDOW,
            STEP
        ):

            crop = image[
                y:y + WINDOW,
                x:x + WINDOW
            ]

            gray = cv2.cvtColor(
                crop,
                cv2.COLOR_BGR2GRAY
            )

            edges = cv2.Canny(
                gray,
                80,
                160
            )

            edge_ratio = (
                (edges > 0).sum()
                /
                edges.size
            )

            if edge_ratio < 0.05:
                continue

            output_path = (
                f"{OUTPUT_DIR}/"
                f"candidate_{index}.png"
            )

            cv2.imwrite(
                output_path,
                crop
            )

            index += 1

    print(
        f"[CANDIDATES] {index}"
    )