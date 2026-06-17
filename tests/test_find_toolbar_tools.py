from pprint import pprint

from app.ui.runtime.find_toolbar_tools import (
    find_toolbar_tools
)

tools = find_toolbar_tools(
    "samples/ui/wh_screen_01.png"
)

print()
print("=" * 80)
print("TOOLS")
print("=" * 80)
print()

pprint(tools)

print()