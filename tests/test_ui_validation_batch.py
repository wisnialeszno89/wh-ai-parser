import os

from app.ui.runtime.find_semantic_tools import (
    find_semantic_tools
)


INPUT_DIR = (
    "samples/ui"
)


for filename in sorted(

    os.listdir(INPUT_DIR)

):

    if not filename.endswith(
        ".png"
    ):
        continue

    path = os.path.join(
        INPUT_DIR,
        filename
    )

    print()
    print("=" * 80)
    print(filename)
    print("=" * 80)

    tools = find_semantic_tools(
        path
    )

    summary = {}

    for tool in tools:

        name = tool["tool"]

        summary[name] = (
            summary.get(
                name,
                0
            )
            + 1
        )

    print()

    print(
        "SUMMARY"
    )

    print(
        "-" * 40
    )

    for name, count in sorted(
        summary.items()
    ):

        print(
            f"{name:<30}"
            f"{count}"
        )

    print()