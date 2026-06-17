from pprint import pprint

from app.ui.runtime.find_semantic_tools import (
    find_semantic_tools
)

tools = find_semantic_tools(
    "samples/ui/wh_screen_06.png"
)

print()
print("=" * 80)
print("FINAL")
print("=" * 80)
print()

pprint(tools)