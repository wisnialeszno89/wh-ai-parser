from app.ui.runtime.find_semantic_tools import (
    find_semantic_tools
)


tools = find_semantic_tools(

    "samples/ui/wh_screen_01.png"
)

print()

for tool in tools[:20]:

    print(
        "=" * 60
    )

    print(
        f"TOOL: "
        f"{tool['tool']}"
    )

    print(
        f"CONF: "
        f"{tool['confidence']:.6f}"
    )

    print()

    for item in tool["top3"]:

        print(
            f"{item['tool']} "
            f"{item['confidence']:.6f}"
        )

print()