from math import sqrt

from app.ui.dataset.extract_icon_candidates import (
    extract_icon_candidates
)

from app.ui.ml.semantic_classifier_v3 import (
    SemanticClassifierV3
)


CONFIDENCE_THRESHOLD = 0.20

DISTANCE_THRESHOLD = 32


def distance(a, b):

    return sqrt(

        (a["x"] - b["x"]) ** 2 +

        (a["y"] - b["y"]) ** 2
    )


def deduplicate_tools(results):

    deduplicated = []

    for candidate in sorted(

        results,

        key=lambda x: x["confidence"],

        reverse=True
    ):

        duplicate = False

        for existing in deduplicated:

            if (

                existing["tool"]

                ==

                candidate["tool"]

            ):

                if distance(

                    existing,

                    candidate

                ) < DISTANCE_THRESHOLD:

                    duplicate = True

                    break

        if not duplicate:

            deduplicated.append(
                candidate
            )

    return deduplicated


def find_semantic_tools(

    screenshot_path: str,

    threshold: float = (
        CONFIDENCE_THRESHOLD
    )
):

    classifier = (
        SemanticClassifierV3()
    )

    candidates = (
        extract_icon_candidates(
            screenshot_path
        )
    )

    results = []

    for candidate in candidates:

        tool, confidence, top3 = (

            classifier.predict_crop(
                candidate["crop"]
            )
        )

        print()
        print("=" * 80)

        print(
            f"x={candidate['x']} "
            f"y={candidate['y']}"
        )

        print(
            f"TOP1: {tool} "
            f"{confidence:.6f}"
        )

        print()

        for item in top3:

            print(
                f"    "
                f"{item['tool']} "
                f"{item['confidence']:.6f}"
            )

        if tool == "non_icon":

            continue

        if confidence < threshold:

            continue

        results.append({

            "tool": tool,

            "confidence": confidence,

            "top3": top3,

            "x": candidate["x"],

            "y": candidate["y"],

            "width": 64,

            "height": 64
        })

    return deduplicate_tools(
        results
    )