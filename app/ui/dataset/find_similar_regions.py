import os
import cv2


print("RUNNING NEW HARVESTER")


OUTPUT_DIR = "outputs/similar_regions"

WINDOW_SIZE = 24
STEP = 4

TOP_K = 30

AUTO_SAVE_THRESHOLD = 0.50


def find_similar_regions(

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
        (
            WINDOW_SIZE,
            WINDOW_SIZE
        )
    )

    height, width = gray.shape

    matches = []

    for y in range(
        0,
        height - WINDOW_SIZE,
        STEP
    ):

        for x in range(
            0,
            width - WINDOW_SIZE,
            STEP
        ):

            crop = gray[
                y:y + WINDOW_SIZE,
                x:x + WINDOW_SIZE
            ]

            result = cv2.matchTemplate(
                crop,
                template_gray,
                cv2.TM_CCOEFF_NORMED
            )

            _, score, _, _ = cv2.minMaxLoc(
                result
            )

            matches.append({

                "x": x,
                "y": y,

                "score": score,

                "crop": crop
            })

    matches = sorted(
        matches,
        key=lambda m: m["score"],
        reverse=True
    )

    top_matches = matches[:TOP_K]

    auto_saved = 0

    for index, match in enumerate(top_matches):

        output_path = (
            f"{OUTPUT_DIR}/"
            f"{template_name}_{index}.png"
        )

        cv2.imwrite(
            output_path,
            match["crop"]
        )

        print(
            f"[MATCH] "
            f"{template_name} "
            f"score={match['score']}"
        )

        if match["score"] >= AUTO_SAVE_THRESHOLD:

            print("SAVING IMAGE")

            dataset_path = (
                f"{dataset_dir}/"
                f"{template_name}_{index}.png"
            )

            cv2.imwrite(
                dataset_path,
                match["crop"]
            )

            auto_saved += 1

    print(
        f"[AUTO SAVED] "
        f"{template_name} "
        f"=> "
        f"{auto_saved}"
    )