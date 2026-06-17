from app.ui.runtime.find_toolbar_tools import (
    find_toolbar_tools
)


def build_toolbar_map(

    screenshot_path: str
):

    tools = find_toolbar_tools(
        screenshot_path
    )

    toolbar_map = {}

    for tool in tools:

        name = tool["tool"]

        if name not in toolbar_map:

            toolbar_map[name] = []

        toolbar_map[name].append({

            "x": tool["x"],

            "y": tool["y"],

            "confidence": tool["confidence"]
        })

    return toolbar_map