from pprint import pprint

from app.ui.runtime.build_toolbar_map import (
    build_toolbar_map
)

toolbar_map = build_toolbar_map(
    "samples/ui/wh_screen_01.png"
)

print()
print("=" * 80)
print("TOOLBAR MAP")
print("=" * 80)
print()

pprint(toolbar_map)

print()