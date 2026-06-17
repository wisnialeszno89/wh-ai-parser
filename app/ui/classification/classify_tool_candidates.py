import cv2

from app.ui.models.ui_object import (
    UIObject
)


TEMPLATES = {

    "frame_tool":
        "templates/frame_tool.png",

    "sash_tool":
        "templates/sash_tool.png",

    "glass_tool":
        "templates/glass_tool.png"
}


THRESHOLD = 0.15

SIZE = 32


def normalize_icon(

    image
):

    gray = cv2.cvtColor(

        image,

        cv2.COLOR_BGR2GRAY
    )

    resized = cv2.resize(

        gray,

        (SIZE, SIZE)
    )

    equalized = cv2.equalizeHist(
        resized
    )

    _, binary = cv2.threshold(

        equalized,

        0,

        255,

        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )

    return binary


def classify_tool_candidates(

    image_path: str,

    candidates
):

    image = cv2.imread(
        image_path
    )

    best_matches = {}

    for candidate in candidates:

        crop = image[

            candidate.y:
            candidate.y + candidate.height,

            candidate.x:
            candidate.x + candidate.width
        ]

        if crop.size == 0:

            continue

        crop_binary = normalize_icon(
            crop
        )

        for label, template_path in TEMPLATES.items():

            template = cv2.imread(
                template_path
            )

            if template is None:

                continue

            template_binary = normalize_icon(
                template
            )

            result = cv2.matchTemplate(

                crop_binary,

                template_binary,

                cv2.TM_CCOEFF_NORMED
            )

            _, score, _, _ = cv2.minMaxLoc(
                result
            )

            print(
                f"[DEBUG] "
                f"{candidate.id} "
                f"vs "
                f"{label} "
                f"score={score}"
            )

            if score < THRESHOLD:

                continue

            current_best = best_matches.get(
                label
            )

            if current_best is None:

                best_matches[label] = {

                    "score": score,

                    "candidate": candidate
                }

            else:

                if score > current_best["score"]:

                    best_matches[label] = {

                        "score": score,

                        "candidate": candidate
                    }

    classified = []

    for label, data in best_matches.items():

        candidate = data["candidate"]

        score = data["score"]

        print(
            f"[BEST MATCH] "
            f"{label} "
            f"=> "
            f"{score}"
        )

        classified.append(

            UIObject(

                id=label,

                object_type="tool",

                x=candidate.x,
                y=candidate.y,

                width=candidate.width,
                height=candidate.height,

                label=label
            )
        )

    return classified