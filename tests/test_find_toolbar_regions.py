from pprint import pprint

from app.ui.runtime.find_toolbar_regions import (
    find_toolbar_regions
)

regions = find_toolbar_regions(
    "samples/ui/wh_screen_01.png"
)

print()

pprint(regions)

print()