from pprint import pprint

from app.ui.runtime.find_toolbar_band import (
    find_toolbar_band
)

regions = find_toolbar_band(
    "samples/ui/wh_screen_01.png"
)

print()

pprint(regions)

print()