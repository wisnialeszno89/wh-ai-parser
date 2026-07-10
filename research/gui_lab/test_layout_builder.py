import cv2

from research.gui_lab.builders.layout_builder import (
    LayoutBuilder,
)

INPUT = "research/gui_lab/input/windowhub.png"


image = cv2.imread(
    INPUT,
)

builder = LayoutBuilder()

layout = builder.build(
    image,
)

print()

print("=" * 60)
print("LAYOUT")
print("=" * 60)

print()

print(f"Panels: {len(layout)}")

print()

for panel in layout:

    fp = panel.fingerprint

    print("-" * 60)

    print(f"Panel {panel.id}")

    print(
        panel.panel
    )

    print(
        fp
    )