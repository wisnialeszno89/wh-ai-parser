import cv2

from app.ui.detection.detect_tool_candidates import (
    detect_tool_candidates
)

from app.ui.classification.classify_tool_candidates import (
    classify_tool_candidates
)

from app.ui.risk.calculate_ui_risk import (
    calculate_ui_risk
)


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

MAX_RISK = 0.7


def render_classified_tools(

    image_path: str,

    output_path: str
):

    image = cv2.imread(
        image_path
    )

    candidates = detect_tool_candidates(
        image_path
    )

    print(
        f"[DEBUG] candidates="
        f"{len(candidates)}"
    )

    tools = classify_tool_candidates(

        image_path,

        candidates
    )

    safe_tools = []

    for tool in tools:

        risk = calculate_ui_risk(

            tool,

            SCREEN_WIDTH,
            SCREEN_HEIGHT
        )

        print(
            f"[RISK] "
            f"{tool.label} "
            f"=> "
            f"{risk}"
        )

        if risk > MAX_RISK:

            print(
                f"[BLOCKED] "
                f"{tool.label}"
            )

            continue

        safe_tools.append(
            tool
        )

    print(
        f"[DEBUG] classified="
        f"{len(safe_tools)}"
    )

    for tool in safe_tools:

        print(
            f"[DRAW] "
            f"{tool.label} "
            f"at "
            f"{tool.x},{tool.y}"
        )

        cv2.rectangle(

            image,

            (tool.x, tool.y),

            (
                tool.x + tool.width,

                tool.y + tool.height
            ),

            (0, 255, 0),

            3
        )

        cv2.putText(

            image,

            tool.label,

            (

                tool.x,

                tool.y - 5
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            (0, 255, 0),

            2
        )

    cv2.imwrite(

        output_path,

        image
    )

    print(
        f"[DEBUG] saved: "
        f"{output_path}"
    )