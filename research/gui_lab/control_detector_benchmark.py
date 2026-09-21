from __future__ import annotations

from collections import Counter
from pathlib import Path

import cv2

from app.runtime.execution.vision.analyzers.control_detector import (
    ControlDetector,
)
from app.runtime.execution.vision.models.control_role import (
    ControlRole,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)
from app.runtime.execution.vision.models.rect import (
    Rect,
)
from app.wh.vision.screenshot import (
    Screenshot,
)


IMAGE_PATHS = [
    Path("tests/data/screenshot.png"),
    Path("research/gui_lab/input/windowhub.png"),
    Path("samples/wh_screen.png"),
    Path("samples/ui/wh_screen_01.png"),
    Path("samples/ui/wh_screen_05.png"),
    Path("samples/ui/wh_screen_10.png"),
]


def collect_nodes(node: GUIObject) -> list[GUIObject]:
    result = [node]

    for child in node.children:
        result.extend(collect_nodes(child))

    return result


def analyze_image(image_path: Path) -> None:
    image = cv2.imread(str(image_path))

    if image is None:
        print(f"ERROR: cannot read {image_path}")
        return

    height, width = image.shape[:2]

    screenshot = Screenshot(
        width=width,
        height=height,
        image=image,
    )

    section = GUIObject(
        id="benchmark_section",
        type=ControlType.SECTION,
        role=ControlRole.UNKNOWN,
        bounds=Rect(
            x=0,
            y=0,
            width=width,
            height=height,
        ),
    )

    detector = ControlDetector()

    detector.analyze(
        screenshot,
        section,
    )

    nodes = []

    for child in section.children:
        nodes.extend(collect_nodes(child))

    counts = Counter(
        node.type
        for node in nodes
    )

    unknown_nodes = [
        node
        for node in nodes
        if node.type == ControlType.UNKNOWN
    ]

    unknown_with_children = [
        node
        for node in unknown_nodes
        if node.children
    ]

    unknown_leaves = [
        node
        for node in unknown_nodes
        if not node.children
    ]

    print("\n" + "=" * 80)
    print(f"IMAGE: {image_path}")
    print(f"RESOLUTION: {width} x {height}")
    print("=" * 80)

    print(f"TOTAL NODES: {len(nodes)}")

    print("\nTYPE COUNTS:")

    for control_type, count in sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0].value),
    ):
        print(
            f"  {control_type.value:12s}: {count}"
        )

    print("\nUNKNOWN:")
    print(f"  total:          {len(unknown_nodes)}")
    print(f"  with children:  {len(unknown_with_children)}")
    print(f"  leaves:         {len(unknown_leaves)}")

    largest_unknown = sorted(
        unknown_nodes,
        key=lambda node: (
            node.bounds.area
            if node.bounds is not None
            else 0
        ),
        reverse=True,
    )[:15]

    print("\nLARGEST UNKNOWN:")

    for index, node in enumerate(
        largest_unknown,
        start=1,
    ):
        if node.bounds is None:
            continue

        rect = node.bounds

        print(
            f"  {index:2d}. "
            f"{rect.width}x{rect.height} "
            f"area={rect.area} "
            f"at=({rect.x},{rect.y}) "
            f"children={len(node.children)} "
            f"confidence={node.confidence:.2f}"
        )


def main() -> None:
    print("\nCONTROL DETECTOR / STRUCTURAL V2 BENCHMARK")

    for image_path in IMAGE_PATHS:
        if not image_path.exists():
            print(
                f"\nSKIP: {image_path} "
                f"(file does not exist)"
            )
            continue

        analyze_image(image_path)

    print("\nBENCHMARK FINISHED\n")


if __name__ == "__main__":
    main()
