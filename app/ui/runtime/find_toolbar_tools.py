from app.ui.runtime.find_toolbar_band import (
    find_toolbar_band
)

from app.ui.detectors.extract_toolbar_slots import (
    extract_toolbar_slots
)

from app.ui.ml.semantic_classifier_v3 import (
    SemanticClassifierV3
)


CONFIDENCE_THRESHOLD = 0.85


def find_toolbar_tools(
    screenshot_path: str
):

    classifier = (
        SemanticClassifierV3()
    )

    bands = find_toolbar_band(
        screenshot_path
    )

    if not bands:

        print(
            "[ERROR] No toolbar found"
        )

        return []

    toolbar = bands[0]

    print()
    print("[TOOLBAR BAND]")
    print(toolbar)
    print()

    toolbar_x = toolbar["x"]

    slots = extract_toolbar_slots(

        screenshot_path,

        toolbar_x
    )

    tools = []

    for slot in slots:

        tool, confidence, top3 = (

            classifier.predict_crop(
                slot["crop"]
            )
        )

        print()

        print(
            f"{slot['y']:>4}px | "
            f"{tool:<25} "
            f"{confidence:.4f}"
        )

        if tool == "non_icon":
            continue

        if confidence < (
            CONFIDENCE_THRESHOLD
        ):
            continue

        tools.append({

            "tool": tool,

            "confidence": confidence,

            "x": slot["x"],

            "y": slot["y"],

            "top3": top3
        })

        print()
        print("=" * 60)

        print(
            f"TOOL: {tool}"
        )

        print(
            f"CONF: "
            f"{confidence:.6f}"
        )

        print()

        for item in top3:

            print(
                f"{item['tool']:<30}"
                f"{item['confidence']:.6f}"
            )

    return tools